import os
import uuid
from datetime import datetime, timezone
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))


def log_complaint(
    extracted_data: dict,
    eligibility: dict,
    decision: dict
) -> dict:
    """
    Logs every resolved complaint into Firestore with full details.
    Builds the product intelligence database automatically.
    """

    complaint_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Build the full complaint record
    record = {
        "complaint_id": complaint_id,
        "timestamp": now,

        # Product details
        "product_name": extracted_data.get("product_name", "Unknown"),
        "order_id": extracted_data.get("order_id", "Not provided"),

        # Complaint details
        "issue_type": extracted_data.get("issue_type", "other"),
        "complaint_summary": extracted_data.get("complaint_summary", ""),
        "urgency_level": extracted_data.get("urgency_level", "medium"),
        "customer_emotion": extracted_data.get("customer_emotion", "neutral"),

        # Eligibility details
        "days_since_purchase": eligibility.get("days_since_purchase"),
        "policy_applied": eligibility.get("policy_applied", ""),

        # Decision details
        "resolution": decision.get("decision", "escalate"),
        "decision_reason": decision.get("decision_reason", ""),
        "priority": decision.get("priority", "medium"),
        "estimated_resolution_days": decision.get("estimated_resolution_days", 3),

        # Tracking fields
        "manufacturer_contacted": False,
        "manufacturer_resolved": False,
        "customer_notified_of_fix": False,
        "is_resolved": True,

        # Metadata
        "created_at": now,
        "updated_at": now
    }

    # Step 1 — Save to complaints collection
    db.collection("complaints").document(complaint_id).set(record)

    # Step 2 — Update product statistics
    update_product_stats(
        product_name=extracted_data.get("product_name", "Unknown"),
        issue_type=extracted_data.get("issue_type", "other"),
        complaint_id=complaint_id
    )

    return {
        "status": "logged",
        "complaint_id": complaint_id,
        "record": record
    }


def update_product_stats(
    product_name: str,
    issue_type: str,
    complaint_id: str
) -> None:
    """
    Updates the product statistics document for pattern detection.
    """

    product_ref = db.collection("product_stats").document(product_name)
    product_doc = product_ref.get()

    if product_doc.exists:
        stats = product_doc.to_dict()
        total = stats.get("total_complaints", 0) + 1
        issue_counts = stats.get("issue_counts", {})
        issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        complaint_ids = stats.get("complaint_ids", [])
        complaint_ids.append(complaint_id)

        product_ref.update({
            "total_complaints": total,
            "issue_counts": issue_counts,
            "complaint_ids": complaint_ids,
            "last_complaint_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    else:
        product_ref.set({
            "product_name": product_name,
            "total_complaints": 1,
            "issue_counts": {issue_type: 1},
            "complaint_ids": [complaint_id],
            "manufacturer_contacted": False,
            "manufacturer_resolved": False,
            "first_complaint_at": datetime.now(timezone.utc),
            "last_complaint_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })


def get_all_complaints() -> list:
    """Returns all complaints from Firestore."""
    docs = db.collection("complaints").order_by(
        "created_at",
        direction=firestore.Query.DESCENDING
    ).limit(100).stream()
    return [doc.to_dict() for doc in docs]


def get_product_stats() -> list:
    """Returns all product statistics."""
    docs = db.collection("product_stats").order_by(
        "total_complaints",
        direction=firestore.Query.DESCENDING
    ).stream()
    return [doc.to_dict() for doc in docs]


def get_complaint_by_id(complaint_id: str) -> dict:
    """Returns a single complaint by ID."""
    doc = db.collection("complaints").document(complaint_id).get()
    return doc.to_dict() if doc.exists else None