import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
db = firestore.Client(project=PROJECT_ID)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def _default_due_date(event_type: str) -> datetime:
    """
    Creates a default due date based on event type.
    """
    now = _utc_now()
    event_type = (event_type or "generic_followup").lower()

    if event_type == "manufacturer_deadline":
        return now + timedelta(days=3)
    if event_type == "tracker_followup":
        return now + timedelta(days=2)
    if event_type == "internal_review":
        return now + timedelta(days=1)
    if event_type == "customer_followup":
        return now + timedelta(days=1)

    return now + timedelta(days=3)


def create_event(
    *,
    title: str,
    event_type: str,
    related_entity: str,
    related_id: str,
    due_at: Optional[datetime] = None,
    description: str = "",
    owner: str = "ResolveX System",
    status: str = "scheduled",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a calendar-style operational event in Firestore.
    """
    event_id = str(uuid.uuid4())
    now = _utc_now()
    final_due_at = due_at or _default_due_date(event_type)

    record = {
        "event_id": event_id,
        "title": title,
        "event_type": event_type,            # manufacturer_deadline / tracker_followup / internal_review / customer_followup
        "related_entity": related_entity,    # complaint / product / manufacturer / task
        "related_id": related_id,
        "description": description,
        "owner": owner,
        "status": status,                    # scheduled / completed / missed / cancelled
        "due_at": final_due_at,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "metadata": metadata or {},
    }

    db.collection("calendar_events").document(event_id).set(record)

    return {
        "status": "created",
        "event": _serialize(record),
    }


def complete_event(event_id: str, note: str = "") -> Dict[str, Any]:
    """
    Marks an event as completed.
    """
    event_ref = db.collection("calendar_events").document(event_id)
    event_doc = event_ref.get()

    if not event_doc.exists:
        return {
            "status": "not_found",
            "event_id": event_id,
            "message": "Calendar event not found.",
        }

    now = _utc_now()
    payload = {
        "status": "completed",
        "completed_at": now,
        "updated_at": now,
    }

    if note:
        payload["completion_note"] = note

    event_ref.update(payload)
    updated_doc = event_ref.get().to_dict()

    return {
        "status": "completed",
        "event": _serialize(updated_doc),
    }


def reschedule_event(event_id: str, new_due_at: datetime, reason: str = "") -> Dict[str, Any]:
    """
    Reschedules an existing event.
    """
    event_ref = db.collection("calendar_events").document(event_id)
    event_doc = event_ref.get()

    if not event_doc.exists:
        return {
            "status": "not_found",
            "event_id": event_id,
            "message": "Calendar event not found.",
        }

    payload = {
        "due_at": new_due_at,
        "updated_at": _utc_now(),
        "status": "scheduled",
    }

    if reason:
        payload["reschedule_reason"] = reason

    event_ref.update(payload)
    updated_doc = event_ref.get().to_dict()

    return {
        "status": "rescheduled",
        "event": _serialize(updated_doc),
    }


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns one calendar event by ID.
    """
    doc = db.collection("calendar_events").document(event_id).get()
    if not doc.exists:
        return None
    return _serialize(doc.to_dict())


def get_upcoming_events(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns upcoming scheduled events.
    """
    now = _utc_now()
    docs = (
        db.collection("calendar_events")
        .where("status", "==", "scheduled")
        .where("due_at", ">=", now)
        .order_by("due_at", direction=firestore.Query.ASCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_overdue_events(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns overdue scheduled events.
    """
    now = _utc_now()
    docs = (
        db.collection("calendar_events")
        .where("status", "==", "scheduled")
        .where("due_at", "<", now)
        .order_by("due_at", direction=firestore.Query.ASCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_events_by_entity(
    related_entity: str,
    related_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Returns events associated with one entity.
    """
    docs = (
        db.collection("calendar_events")
        .where("related_entity", "==", related_entity)
        .where("related_id", "==", related_id)
        .order_by("due_at", direction=firestore.Query.ASCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_calendar_summary(limit: int = 200) -> Dict[str, Any]:
    """
    Returns calendar summary counts for dashboard.
    """
    docs = (
        db.collection("calendar_events")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    events = [_serialize(doc.to_dict()) for doc in docs]
    now = _utc_now()

    summary = {
        "total_events": len(events),
        "scheduled": 0,
        "completed": 0,
        "missed": 0,
        "cancelled": 0,
        "overdue": 0,
        "manufacturer_deadline": 0,
        "tracker_followup": 0,
        "internal_review": 0,
        "customer_followup": 0,
    }

    for event in events:
        status = event.get("status", "scheduled")
        event_type = event.get("event_type", "generic_followup")

        if status in summary:
            summary[status] += 1

        if event_type in summary:
            summary[event_type] += 1

        due_at_raw = event.get("due_at")
        try:
            if isinstance(due_at_raw, str):
                due_at = datetime.fromisoformat(due_at_raw)
                if due_at.tzinfo is None:
                    due_at = due_at.replace(tzinfo=timezone.utc)
                if status == "scheduled" and due_at < now:
                    summary["overdue"] += 1
        except Exception:
            pass

    return summary


if __name__ == "__main__":
    result = create_event(
        title="Manufacturer response deadline for Voltix Charger",
        event_type="manufacturer_deadline",
        related_entity="product",
        related_id="Voltix Charger",
        description="Wait for manufacturer response regarding repeated defect complaints.",
        owner="ResolveX Manufacturer Agent",
        metadata={
            "severity": "high",
            "complaint_count": 5,
        },
    )

    print("Created Calendar Event:")
    print(result)