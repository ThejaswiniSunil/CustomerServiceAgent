import os
import logging
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

# Setup logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe initialization
_project = os.getenv("GOOGLE_CLOUD_PROJECT")
_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

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


def track_and_followup(product_name: str) -> dict:
    """
    Checks manufacturer response status.
    Sends follow-ups if no response.
    Notifies customers when issue is resolved.
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

    # Step 2 — If already resolved, notify customers
    if issue_resolved:
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
    Generates and sends a follow-up message to manufacturer.
    Increments follow-up counter only after successful generation.
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

    # Step 2 — Update Firestore only after successful generation
    try:
        db.collection("manufacturer_contacts").document(product_name).update({
            "follow_up_count": follow_up_count + 1,
            "last_followup_at": datetime.now(timezone.utc),
            "last_followup_body": followup_body,
            "updated_at": datetime.now(timezone.utc)
        })
        logger.info(f"[tracker_agent] Follow-up count updated to {follow_up_count + 1}")
    except Exception as e:
        logger.error(f"[tracker_agent] Follow-up Firestore update failed: {e}")

    return {
        "status": "followup_sent",
        "product_name": product_name,
        "follow_up_number": follow_up_count + 1,
        "followup_body": followup_body
    }


def mark_resolved(product_name: str) -> dict:
    """
    Marks a manufacturer issue as resolved.
    Called when manufacturer confirms fix.
    Triggers customer notifications automatically.
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

    # Step 3 — Notify all affected customers
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
            complaint_id = complaint.get("complaint_id")
            complaint_summary = complaint.get("complaint_summary", "a product issue")

            # Validate complaint_id before proceeding
            if not complaint_id:
                logger.warning("[tracker_agent] Complaint missing complaint_id — skipping")
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

            # Step 3 — Update complaint record
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