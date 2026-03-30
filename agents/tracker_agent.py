import os
import json
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)

model = GenerativeModel("gemini-2.0-flash-001")
db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

MAX_FOLLOW_UPS = int(os.getenv("MAX_FOLLOW_UPS", "3"))


def track_and_followup(product_name: str) -> dict:
    """
    Checks manufacturer response status.
    Sends follow-ups if no response.
    Notifies customers when issue is resolved.
    """

    # Step 1 — Get manufacturer contact record
    contact_ref = db.collection("manufacturer_contacts").document(product_name)
    contact_doc = contact_ref.get()

    if not contact_doc.exists:
        return {
            "status": "not_found",
            "product_name": product_name,
            "message": "No manufacturer contact record found"
        }

    contact = contact_doc.to_dict()
    issue_resolved = contact.get("issue_resolved", False)
    follow_up_count = contact.get("follow_up_count", 0)

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
        followup_result = send_followup(product_name, contact, follow_up_count)
        return followup_result

    # Step 4 — Max follow-ups reached, escalate
    db.collection("manufacturer_contacts").document(product_name).update({
        "escalated": True,
        "escalated_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    return {
        "status": "escalated",
        "product_name": product_name,
        "follow_up_count": follow_up_count,
        "message": "Maximum follow-ups reached. Escalated for manual review."
    }


def send_followup(product_name: str, contact: dict, follow_up_count: int) -> dict:
    """Generates and sends a follow-up message to manufacturer."""

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

    # Update follow-up count in Firestore
    db.collection("manufacturer_contacts").document(product_name).update({
        "follow_up_count": follow_up_count + 1,
        "last_followup_at": datetime.now(timezone.utc),
        "last_followup_body": followup_body,
        "updated_at": datetime.now(timezone.utc)
    })

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
    """

    db.collection("manufacturer_contacts").document(product_name).update({
        "issue_resolved": True,
        "resolved_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    db.collection("product_stats").document(product_name).update({
        "manufacturer_resolved": True,
        "manufacturer_resolved_at": datetime.now(timezone.utc)
    })

    # Notify all affected customers
    notified = notify_customers(product_name)

    return {
        "status": "marked_resolved",
        "product_name": product_name,
        "customers_notified": notified
    }


def notify_customers(product_name: str) -> int:
    """
    Notifies all customers who complained about this product
    that their issue has been fixed at the source.
    """

    # Get all complaints for this product
    complaints = (
        db.collection("complaints")
        .where("product_name", "==", product_name)
        .where("customer_notified_of_fix", "==", False)
        .stream()
    )

    notified_count = 0

    for complaint_doc in complaints:
        complaint = complaint_doc.to_dict()
        order_id = complaint.get("order_id", "")
        complaint_summary = complaint.get("complaint_summary", "")

        # Generate personalized closing message
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

        # Update complaint record
        db.collection("complaints").document(
            complaint.get("complaint_id")
        ).update({
            "customer_notified_of_fix": True,
            "closing_message": closing_message,
            "loop_closed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        notified_count += 1

    return notified_count