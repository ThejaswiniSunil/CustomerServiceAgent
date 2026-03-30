import os
import json
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)

model = GenerativeModel("gemini-2.0-flash-001")
db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))


def contact_manufacturer(insight_report: dict) -> dict:
    """
    Contacts the manufacturer with a full data-backed report
    and logs the communication in Firestore.
    """

    product_name = insight_report.get("product_name", "Unknown")
    email_subject = insight_report.get("manufacturer_email_subject", "")
    email_body = insight_report.get("manufacturer_email_body", "")
    severity_level = insight_report.get("severity_level", "high")
    total_complaints = insight_report.get("total_complaints", 0)

    # Step 1 — Get manufacturer contact from Firestore
    manufacturer_email = get_manufacturer_email(product_name)

    # Step 2 — Send email to manufacturer
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
        except Exception as e:
            email_error = str(e)
    else:
        # Log that no manufacturer email was found
        email_error = "Manufacturer email not found in database"

    # Step 3 — Log manufacturer contact in Firestore
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
        "contacted_at": datetime.now(timezone.utc),
        "follow_up_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    db.collection("manufacturer_contacts").document(product_name).set(contact_record)

    # Step 4 — Update product stats
    db.collection("product_stats").document(product_name).update({
        "manufacturer_contacted": True,
        "manufacturer_contacted_at": datetime.now(timezone.utc)
    })

    return {
        "status": "contacted" if email_sent else "logged",
        "product_name": product_name,
        "manufacturer_email": manufacturer_email,
        "email_sent": email_sent,
        "email_error": email_error,
        "contact_record": contact_record
    }


def get_manufacturer_email(product_name: str) -> str:
    """Gets manufacturer email from Firestore manufacturers collection."""
    try:
        doc = db.collection("manufacturers").document(product_name).get()
        if doc.exists:
            return doc.to_dict().get("email")
    except Exception:
        pass

    # Fallback to env variable for demo
    return os.getenv("MANUFACTURER_EMAIL", "manufacturer@demo.com")


def send_email(to_email: str, subject: str, body: str) -> None:
    """Sends email via SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP credentials not configured")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def get_pending_contacts() -> list:
    """Returns all manufacturer contacts that are unresolved."""
    docs = (
        db.collection("manufacturer_contacts")
        .where("issue_resolved", "==", False)
        .stream()
    )
    return [doc.to_dict() for doc in docs]