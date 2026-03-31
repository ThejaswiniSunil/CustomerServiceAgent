import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
db = firestore.Client(project=PROJECT_ID)


def _utc_now():
    return datetime.now(timezone.utc)


def _safe_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def serialize_firestore_doc(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts Firestore-friendly objects into dashboard/API-friendly output.
    """
    serialized = {}

    for key, value in data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_firestore_doc(value)
        elif isinstance(value, list):
            serialized[key] = [
                serialize_firestore_doc(item) if isinstance(item, dict)
                else item.isoformat() if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            serialized[key] = value

    return serialized


def build_complaint_record(
    extracted_data: Dict[str, Any],
    eligibility: Dict[str, Any],
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates a normalized complaint record for Firestore.
    """
    complaint_id = str(uuid.uuid4())
    now = _utc_now()

    order_snapshot = eligibility.get("order_snapshot") or {}

    record = {
        "complaint_id": complaint_id,
        "product_name": _safe_string(extracted_data.get("product_name"), "Unknown"),
        "order_id": _safe_string(extracted_data.get("order_id"), "Not provided"),
        "issue_type": _safe_string(extracted_data.get("issue_type"), "other"),
        "complaint_summary": _safe_string(extracted_data.get("complaint_summary"), ""),
        "urgency_level": _safe_string(extracted_data.get("urgency_level"), "medium"),
        "customer_emotion": _safe_string(extracted_data.get("customer_emotion"), "neutral"),

        "order_found": bool(eligibility.get("order_found", False)),
        "product_match": bool(eligibility.get("product_match", False)),
        "days_since_purchase": eligibility.get("days_since_purchase"),
        "return_window_days": _safe_int(eligibility.get("return_window_days"), 7),
        "within_return_window": bool(eligibility.get("within_return_window", False)),
        "warranty_status": _safe_string(eligibility.get("warranty_status"), "unknown"),
        "policy_applied": _safe_string(eligibility.get("policy_applied"), ""),
        "eligible_for": _safe_string(eligibility.get("eligible_for"), "manual_review"),
        "eligibility_reason": _safe_string(eligibility.get("reason"), ""),

        "resolution": _safe_string(decision.get("decision"), "escalate"),
        "decision_reason": _safe_string(decision.get("decision_reason"), ""),
        "priority": _safe_string(decision.get("priority"), "medium"),
        "next_action": _safe_string(decision.get("next_action"), ""),
        "estimated_resolution_days": _safe_int(decision.get("estimated_resolution_days"), 3),
        "customer_message": _safe_string(decision.get("customer_message"), ""),

        "seller": _safe_string(order_snapshot.get("seller"), "Unknown"),
        "price": order_snapshot.get("price"),
        "currency": _safe_string(order_snapshot.get("currency"), "USD"),

        "manufacturer_contacted": False,
        "manufacturer_resolved": False,
        "customer_notified_of_fix": False,
        "is_resolved": True,

        "created_at": now,
        "updated_at": now,
    }

    return record


def log_complaint(
    extracted_data: Dict[str, Any],
    eligibility: Dict[str, Any],
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Logs a complaint and updates product stats.
    """
    record = build_complaint_record(extracted_data, eligibility, decision)
    complaint_id = record["complaint_id"]

    db.collection("complaints").document(complaint_id).set(record)

    update_product_stats(
        product_name=record["product_name"],
        issue_type=record["issue_type"],
        complaint_id=complaint_id,
        priority=record["priority"],
        resolution=record["resolution"],
    )

    return {
        "status": "logged",
        "complaint_id": complaint_id,
        "record": serialize_firestore_doc(record),
    }


def update_product_stats(
    product_name: str,
    issue_type: str,
    complaint_id: str,
    priority: str,
    resolution: str,
) -> None:
    """
    Updates product-level aggregate statistics for insights and dashboard.
    """
    now = _utc_now()
    product_ref = db.collection("product_stats").document(product_name)
    product_doc = product_ref.get()

    if product_doc.exists:
        stats = product_doc.to_dict()

        total_complaints = _safe_int(stats.get("total_complaints"), 0) + 1

        issue_counts = stats.get("issue_counts", {})
        issue_counts[issue_type] = _safe_int(issue_counts.get(issue_type), 0) + 1

        priority_counts = stats.get("priority_counts", {})
        priority_counts[priority] = _safe_int(priority_counts.get(priority), 0) + 1

        resolution_counts = stats.get("resolution_counts", {})
        resolution_counts[resolution] = _safe_int(resolution_counts.get(resolution), 0) + 1

        complaint_ids = stats.get("complaint_ids", [])
        if complaint_id not in complaint_ids:
            complaint_ids.append(complaint_id)

        product_ref.update({
            "total_complaints": total_complaints,
            "issue_counts": issue_counts,
            "priority_counts": priority_counts,
            "resolution_counts": resolution_counts,
            "complaint_ids": complaint_ids,
            "last_complaint_at": now,
            "updated_at": now,
        })
    else:
        product_ref.set({
            "product_name": product_name,
            "total_complaints": 1,
            "issue_counts": {issue_type: 1},
            "priority_counts": {priority: 1},
            "resolution_counts": {resolution: 1},
            "complaint_ids": [complaint_id],
            "manufacturer_contacted": False,
            "manufacturer_resolved": False,
            "pattern_detected": False,
            "first_complaint_at": now,
            "last_complaint_at": now,
            "created_at": now,
            "updated_at": now,
        })


def get_all_complaints(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns recent complaints ordered by latest first.
    """
    docs = (
        db.collection("complaints")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [serialize_firestore_doc(doc.to_dict()) for doc in docs]


def get_product_stats() -> List[Dict[str, Any]]:
    """
    Returns all product statistics ordered by highest complaint volume.
    """
    docs = (
        db.collection("product_stats")
        .order_by("total_complaints", direction=firestore.Query.DESCENDING)
        .stream()
    )

    return [serialize_firestore_doc(doc.to_dict()) for doc in docs]


def get_complaint_by_id(complaint_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns one complaint by ID.
    """
    doc = db.collection("complaints").document(complaint_id).get()
    if not doc.exists:
        return None
    return serialize_firestore_doc(doc.to_dict())


def get_product_stat_by_name(product_name: str) -> Optional[Dict[str, Any]]:
    """
    Returns one product stats record by product name.
    """
    doc = db.collection("product_stats").document(product_name).get()
    if not doc.exists:
        return None
    return serialize_firestore_doc(doc.to_dict())


if __name__ == "__main__":
    sample_extracted_data = {
        "product_name": "Voltix Charger",
        "order_id": "ORD001",
        "issue_type": "defect",
        "complaint_summary": "The charger overheats and stopped working.",
        "urgency_level": "high",
        "customer_emotion": "frustrated",
    }

    sample_eligibility = {
        "order_found": True,
        "product_match": True,
        "days_since_purchase": 3,
        "return_window_days": 7,
        "within_return_window": True,
        "warranty_status": "valid",
        "policy_applied": "defect_under_warranty_policy",
        "eligible_for": "replacement",
        "reason": "The product is defective and the warranty is still valid.",
        "order_snapshot": {
            "order_id": "ORD001",
            "customer_id": "C001",
            "product_name": "Voltix Charger",
            "purchase_date": "2026-03-27",
            "seller": "ResolveX Store",
            "price": 29.99,
            "currency": "USD",
        },
    }

    sample_decision = {
        "decision": "replacement",
        "decision_reason": "The complaint is eligible for replacement under warranty.",
        "priority": "high",
        "next_action": "A replacement request will be initiated.",
        "estimated_resolution_days": 2,
        "customer_message": "We’re sorry for the inconvenience. We’ve approved a replacement and will process it shortly.",
    }

    result = log_complaint(sample_extracted_data, sample_eligibility, sample_decision)
    print("Database Agent Result:")
    print(result)