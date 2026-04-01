import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# MCP tool — calendar events
from mcp.calendar_tool import create_event, complete_event, get_events_by_entity

load_dotenv()

# Setup logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe initialization
_project = os.getenv("GOOGLE_CLOUD_PROJECT")
_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# SMTP config — matches your existing .env
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MANUFACTURER_EMAIL = os.getenv("MANUFACTURER_EMAIL")

if not _project:
    logger.warning("GOOGLE_CLOUD_PROJECT not set — Vertex AI will not initialize")
else:
    vertexai.init(project=_project, location=_location)

model = GenerativeModel("gemini-2.5-flash")
db = firestore.Client(project=_project)

# Safe env var parsing
try:
    MAX_FOLLOW_UPS = int(os.getenv("MAX_FOLLOW_UPS", "3"))
except ValueError:
    MAX_FOLLOW_UPS = 3
    logger.warning("MAX_FOLLOW_UPS env var invalid — defaulting to 3")


def _send_email(to_address: str, subject: str, body: str) -> bool:
    """
    Sends email via Gmail SMTP using credentials from .env.
    Uses SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
    Returns True if sent successfully, False otherwise.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("[tracker_agent] SMTP credentials not set — skipping email send")
        return False

    if not to_address:
        logger.warning("[tracker_agent] No recipient address — skipping email send")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_address, msg.as_string())

        logger.info(f"[tracker_agent] Email sent to {to_address}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("[tracker_agent] SMTP authentication failed — check SMTP_PASSWORD in .env")
        return False
    except Exception as e:
        logger.error(f"[tracker_agent] Email send failed: {e}")
        return False


def track_and_followup(product_name: str) -> dict:
    """
    Checks manufacturer response status.
    Sends follow-ups if no response.
    Notifies customers when issue is resolved.

    MCP tools used:
      - calendar_tool.create_event: schedules next follow-up reminder
      - calendar_tool.complete_event: clears reminder when issue resolved
    """

    logger.info(f"[tracker_agent] Tracking product: {product_name}")

    # Step 1 — Get manufacturer contact record safely
    try:
        contact_ref = db.collection("manufacturer_contacts").document(product_name)
        contact_doc = contact_ref.get()
    except Exception as e:
        logger.error(f"[tracker_agent] Firestore read failed: {e}")
        return {
            "status": "error",
            "product_name": product_name,
            "message": f"Database read failed: {str(e)}"
        }

    if not contact_doc.exists:
        logger.warning(f"[tracker_agent] No contact record found for {product_name}")
        return {
            "status": "not_found",
            "product_name": product_name,
            "message": "No manufacturer contact record found"
        }

    contact = contact_doc.to_dict()
    issue_resolved = contact.get("issue_resolved", False)
    follow_up_count = contact.get("follow_up_count", 0)

    logger.info(
        f"[tracker_agent] {product_name} — "
        f"resolved={issue_resolved}, follow_ups={follow_up_count}"
    )

    # Step 2 — If already resolved, complete calendar events and notify customers
    if issue_resolved:
        # MCP: mark open follow-up events as completed
        try:
            open_events = get_events_by_entity(
                related_entity="product",
                related_id=product_name
            )
            for event in open_events:
                if event.get("status") == "scheduled":
                    complete_event(
                        event_id=event["event_id"],
                        note=f"Issue resolved for {product_name} — follow-up no longer needed"
                    )
                    logger.info(f"[tracker_agent] MCP calendar event completed: {event['event_id']}")
        except Exception as e:
            logger.error(f"[tracker_agent] MCP complete_event failed: {e}")

        notified = notify_customers(product_name)
        return {
            "status": "resolved",
            "product_name": product_name,
            "customers_notified": notified,
            "message": "Issue resolved, customers notified"
        }

    # Step 3 — Send follow-up if under max limit
    if follow_up_count < MAX_FOLLOW_UPS:
        return send_followup(product_name, contact, follow_up_count)

    # Step 4 — Max follow-ups reached, escalate
    try:
        db.collection("manufacturer_contacts").document(product_name).update({
            "escalated": True,
            "escalated_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        logger.warning(f"[tracker_agent] {product_name} escalated after {follow_up_count} follow-ups")
    except Exception as e:
        logger.error(f"[tracker_agent] Escalation update failed: {e}")

    return {
        "status": "escalated",
        "product_name": product_name,
        "follow_up_count": follow_up_count,
        "message": "Maximum follow-ups reached. Escalated for manual review."
    }


def send_followup(product_name: str, contact: dict, follow_up_count: int) -> dict:
    """
    Generates and sends a follow-up email to the manufacturer via Gmail SMTP.
    Schedules next reminder via MCP calendar_tool.create_event().
    """

    logger.info(f"[tracker_agent] Sending follow-up #{follow_up_count + 1} for {product_name}")

    # Step 1 — Generate follow-up email with Gemini
    followup_body = None
    try:
        followup_prompt = f"""
        You are a customer service manager following up with a manufacturer.

        Product: {product_name}
        Previous follow-ups sent: {follow_up_count}
        Total complaints: {contact.get('total_complaints', 0)}
        Severity: {contact.get('severity_level', 'high')}
        Originally contacted at: {contact.get('contacted_at')}

        Write a professional follow-up email body that:
        - References the previous communication
        - Increases urgency appropriately based on follow-up number
        - Demands a response with a clear deadline
        - Remains professional but firm
        - Is 2-3 paragraphs

        Return ONLY the email body text, no subject line, no JSON.
        """
        followup_response = model.generate_content(followup_prompt)
        followup_body = followup_response.text.strip()
    except Exception as e:
        logger.error(f"[tracker_agent] Gemini follow-up generation failed: {e}")
        followup_body = (
            f"Dear Manufacturer,\n\n"
            f"This is follow-up #{follow_up_count + 1} regarding the ongoing quality "
            f"issue with {product_name}. We have still not received a response to our "
            f"previous communications.\n\n"
            f"We require an immediate response and resolution plan. "
            f"Failure to respond within 48 hours will result in further escalation.\n\n"
            f"Regards,\nResolveX Customer Care Team"
        )

    # Step 2 — Send email to manufacturer via Gmail SMTP
    subject = f"[Follow-up #{follow_up_count + 1}] Urgent: Quality Issue — {product_name}"
    email_sent = _send_email(
        to_address=MANUFACTURER_EMAIL,
        subject=subject,
        body=followup_body
    )

    # Step 3 — Update Firestore only after successful generation
    try:
        db.collection("manufacturer_contacts").document(product_name).update({
            "follow_up_count": follow_up_count + 1,
            "last_followup_at": datetime.now(timezone.utc),
            "last_followup_body": followup_body,
            "email_sent": email_sent,
            "updated_at": datetime.now(timezone.utc)
        })
        logger.info(f"[tracker_agent] Follow-up count updated to {follow_up_count + 1}")
    except Exception as e:
        logger.error(f"[tracker_agent] Follow-up Firestore update failed: {e}")

    # Step 4 — MCP: schedule next follow-up reminder via calendar_tool.create_event()
    calendar_result = {}
    try:
        calendar_result = create_event(
            title=f"Follow-up #{follow_up_count + 2} due — {product_name}",
            event_type="tracker_followup",
            related_entity="product",
            related_id=product_name,
            description=(
                f"Manufacturer has not responded after {follow_up_count + 1} follow-up(s). "
                f"Next follow-up required in 3 days."
            ),
            owner="ResolveX Tracker Agent",
            metadata={
                "follow_up_number": follow_up_count + 2,
                "total_complaints": contact.get("total_complaints", 0),
                "severity": contact.get("severity_level", "high"),
            }
        )
        logger.info(f"[tracker_agent] MCP calendar event created: {calendar_result.get('event', {}).get('event_id')}")
    except Exception as e:
        logger.error(f"[tracker_agent] MCP create_event failed: {e}")

    return {
        "status": "followup_sent",
        "product_name": product_name,
        "follow_up_number": follow_up_count + 1,
        "followup_body": followup_body,
        "email_sent": email_sent,
        "next_reminder": calendar_result.get("event", {}).get("due_at")
    }


def mark_resolved(product_name: str) -> dict:
    """
    Marks a manufacturer issue as resolved.
    Completes MCP calendar events and notifies all customers.
    """

    logger.info(f"[tracker_agent] Marking resolved: {product_name}")

    # Step 1 — Update manufacturer contact record
    try:
        db.collection("manufacturer_contacts").document(product_name).update({
            "issue_resolved": True,
            "resolved_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    except Exception as e:
        logger.error(f"[tracker_agent] manufacturer_contacts update failed: {e}")
        return {
            "status": "error",
            "product_name": product_name,
            "message": f"Failed to mark resolved: {str(e)}"
        }

    # Step 2 — Update product stats
    try:
        db.collection("product_stats").document(product_name).update({
            "manufacturer_resolved": True,
            "manufacturer_resolved_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    except Exception as e:
        logger.error(f"[tracker_agent] product_stats update failed: {e}")

    # Step 3 — MCP: complete all open calendar events for this product
    try:
        open_events = get_events_by_entity(related_entity="product", related_id=product_name)
        for event in open_events:
            if event.get("status") == "scheduled":
                complete_event(
                    event_id=event["event_id"],
                    note=f"Issue resolved for {product_name}"
                )
                logger.info(f"[tracker_agent] MCP calendar event completed: {event['event_id']}")
    except Exception as e:
        logger.error(f"[tracker_agent] MCP complete_event failed: {e}")

    # Step 4 — Notify all affected customers
    notified = notify_customers(product_name)
    logger.info(f"[tracker_agent] {notified} customers notified for {product_name}")

    return {
        "status": "marked_resolved",
        "product_name": product_name,
        "customers_notified": notified
    }


def notify_customers(product_name: str) -> int:
    """
    Notifies all customers who complained about this product
    that their issue has been fixed at the source.
    Sends personalized Gmail to each customer if customer_email exists.
    Returns count of successfully notified customers.
    """

    logger.info(f"[tracker_agent] Notifying customers for: {product_name}")

    # Step 1 — Fetch all unnotified complaints for this product
    try:
        complaints_query = (
            db.collection("complaints")
            .where("product_name", "==", product_name)
            .where("customer_notified_of_fix", "==", False)
            .stream()
        )
        complaints = list(complaints_query)
    except Exception as e:
        logger.error(f"[tracker_agent] Failed to fetch complaints: {e}")
        return 0

    notified_count = 0

    for complaint_doc in complaints:
        try:
            complaint = complaint_doc.to_dict()
            complaint_id = complaint_doc.id  # use Firestore doc ID, not field value
            complaint_summary = complaint.get("complaint_summary", "a product issue")
            customer_email = complaint.get("customer_email")

            if not complaint_id:
                logger.warning("[tracker_agent] Complaint missing doc ID — skipping")
                continue

            # Step 2 — Generate personalized closing message
            try:
                message_prompt = f"""
                You are a warm customer service agent.

                A customer complained about: {complaint_summary}
                Product: {product_name}

                The manufacturer has now fixed the underlying issue.

                Write a warm, genuine closing message to the customer that:
                - Thanks them for reporting the issue
                - Tells them the product fault has been identified and fixed
                - Makes them feel their complaint genuinely made a difference
                - Is 3-4 sentences
                - Sounds human and sincere
                """
                message_response = model.generate_content(message_prompt)
                closing_message = message_response.text.strip()
            except Exception as e:
                logger.error(f"[tracker_agent] Gemini message generation failed for {complaint_id}: {e}")
                closing_message = (
                    f"Thank you for reporting the issue with your {product_name}. "
                    f"We are happy to let you know that the problem has been identified "
                    f"and resolved by the manufacturer. Your feedback genuinely made a difference."
                )

            # Step 3 — Send email to customer if email address exists
            if customer_email:
                _send_email(
                    to_address=customer_email,
                    subject=f"Your {product_name} complaint has been resolved ✓",
                    body=closing_message
                )
            else:
                logger.warning(f"[tracker_agent] No customer_email for complaint {complaint_id} — skipping email")

            # Step 4 — Update complaint record
            try:
                db.collection("complaints").document(complaint_id).update({
                    "customer_notified_of_fix": True,
                    "closing_message": closing_message,
                    "loop_closed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                notified_count += 1
                logger.info(f"[tracker_agent] Customer notified for complaint {complaint_id}")
            except Exception as e:
                logger.error(f"[tracker_agent] Failed to update complaint {complaint_id}: {e}")

        except Exception as e:
            logger.error(f"[tracker_agent] Unexpected error processing complaint: {e}")
            continue

    logger.info(f"[tracker_agent] Total customers notified: {notified_count}")
    return notified_count