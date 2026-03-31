import os
import json
import logging
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Setup logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe Vertex AI initialization
_project = os.getenv("GOOGLE_CLOUD_PROJECT")
_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not _project:
    logger.warning("GOOGLE_CLOUD_PROJECT not set — Vertex AI will not initialize")
else:
    vertexai.init(project=_project, location=_location)

model = GenerativeModel("gemini-2.5-flash")
db = firestore.Client(project=_project)


def contact_manufacturer(insight_report: dict) -> dict:
    """
    Contacts the manufacturer with a full data-backed report
    and logs the communication in Firestore.
    """

    product_name = insight_report.get("product_name", "Unknown")
    severity_level = insight_report.get("severity_level", "high")
    total_complaints = insight_report.get("total_complaints", 0)

    logger.info(f"[manufacturer_agent] Contacting manufacturer for: {product_name}")

    # Step 1 — Get manufacturer email safely
    manufacturer_email = get_manufacturer_email(product_name)

    # Step 2 — Get or generate email subject and body
    email_subject = insight_report.get("manufacturer_email_subject") or \
        f"Urgent Quality Issue: {product_name} — {total_complaints} Customer Complaints"

    email_body = insight_report.get("manufacturer_email_body") or \
        _generate_email_body(product_name, insight_report)

    # Validate email content before sending
    if not email_body or len(email_body.strip()) < 20:
        email_body = _generate_email_body(product_name, insight_report)

    # Step 3 — Send email to manufacturer
    email_sent = False
    email_error = None

    if manufacturer_email:
        try:
            send_email(
                to_email=manufacturer_email,
                subject=email_subject,
                body=email_body
            )
            email_sent = True
            logger.info(f"[manufacturer_agent] Email sent to {manufacturer_email}")
        except Exception as e:
            email_error = str(e)
            logger.error(f"[manufacturer_agent] Email failed: {e}")
    else:
        email_error = "Manufacturer email not found in database"
        logger.warning(f"[manufacturer_agent] No email found for {product_name}")

    # Step 4 — Log contact record to Firestore
    contact_record = {
        "product_name": product_name,
        "manufacturer_email": manufacturer_email,
        "email_subject": email_subject,
        "email_body": email_body,
        "severity_level": severity_level,
        "total_complaints": total_complaints,
        "email_sent": email_sent,
        "email_error": email_error,
        "response_received": False,
        "issue_resolved": False,
        "escalated": False,
        "contacted_at": datetime.now(timezone.utc),
        "follow_up_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # Step 5 — Save to Firestore with error handling
    try:
        db.collection("manufacturer_contacts").document(product_name).set(contact_record)
        logger.info(f"[manufacturer_agent] Contact record saved for {product_name}")
    except Exception as e:
        logger.error(f"[manufacturer_agent] Firestore set failed: {e}")
        contact_record["db_error"] = str(e)

    # Step 6 — Update product stats with error handling
    try:
        db.collection("product_stats").document(product_name).update({
            "manufacturer_contacted": True,
            "manufacturer_contacted_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    except Exception as e:
        logger.error(f"[manufacturer_agent] Product stats update failed: {e}")

    return {
        "status": "contacted" if email_sent else "logged",
        "product_name": product_name,
        "manufacturer_email": manufacturer_email,
        "email_sent": email_sent,
        "email_error": email_error,
        "contact_record": contact_record
    }


def _generate_email_body(product_name: str, insight_report: dict) -> str:
    """
    Generates a professional manufacturer email using Gemini
    when one is not provided by the insight agent.
    """
    try:
        prompt = f"""
        Write a professional, firm email to a manufacturer about a product quality issue.

        Product: {product_name}
        Total complaints received: {insight_report.get('total_complaints', 0)}
        Dominant issue: {insight_report.get('dominant_issue', 'defect')}
        Severity: {insight_report.get('severity_level', 'high')}
        Pattern summary: {insight_report.get('pattern_summary', 'Multiple customers reporting the same issue')}

        The email should:
        - State the problem clearly with the complaint data provided
        - Demand a written response and resolution plan within 7 days
        - Mention that continued inaction may result in escalation
        - Be professional, data-driven, and urgent in tone
        - Be 3-4 paragraphs

        Return only the email body. No subject line. No JSON.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"[manufacturer_agent] Email generation failed: {e}")
        return (
            f"Dear Manufacturer,\n\n"
            f"We have received {insight_report.get('total_complaints', 0)} "
            f"customer complaints regarding {product_name}. "
            f"The primary issue reported is: {insight_report.get('dominant_issue', 'product defect')}.\n\n"
            f"We request an urgent response and resolution plan within 7 days.\n\n"
            f"Regards,\nResolveX Customer Care Team"
        )


def get_manufacturer_email(product_name: str) -> str:
    """
    Gets manufacturer email from Firestore.
    Falls back to environment variable if not found.
    """
    try:
        doc = db.collection("manufacturers").document(product_name).get()
        if doc.exists:
            data = doc.to_dict()
            email = data.get("email")
            if email and "@" in email:
                return email
            logger.warning(f"[manufacturer_agent] Invalid email in Firestore for {product_name}")
    except Exception as e:
        logger.error(f"[manufacturer_agent] Firestore email lookup failed: {e}")

    # Fallback to env variable
    fallback = os.getenv("MANUFACTURER_EMAIL", "manufacturer@demo.com")
    logger.info(f"[manufacturer_agent] Using fallback email: {fallback}")
    return fallback


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Sends email to manufacturer via SMTP.
    Raises exception if credentials are missing or send fails.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP credentials not configured in environment variables")

    if not to_email or "@" not in to_email:
        raise ValueError(f"Invalid recipient email address: {to_email}")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        logger.info(f"[manufacturer_agent] SMTP send successful to {to_email}")


def get_pending_contacts() -> list:
    """
    Returns all manufacturer contacts where issue is not yet resolved.
    Returns empty list on error.
    """
    try:
        docs = (
            db.collection("manufacturer_contacts")
            .where("issue_resolved", "==", False)
            .stream()
        )
        results = [doc.to_dict() for doc in docs]
        logger.info(f"[manufacturer_agent] Found {len(results)} pending contacts")
        return results
    except Exception as e:
        logger.error(f"[manufacturer_agent] get_pending_contacts failed: {e}")
        return []