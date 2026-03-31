import os
import uuid
from datetime import datetime, timezone
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


def create_note(
    *,
    title: str,
    note_type: str,
    related_entity: str,
    related_id: str,
    body: str,
    author: str = "ResolveX System",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a structured note in Firestore.
    """
    note_id = str(uuid.uuid4())
    now = _utc_now()

    record = {
        "note_id": note_id,
        "title": title,
        "note_type": note_type,            # complaint_log / analyst_note / decision_note / manufacturer_note / tracker_note / dashboard_note
        "related_entity": related_entity,  # complaint / product / manufacturer / task
        "related_id": related_id,
        "body": body,
        "author": author,
        "tags": tags or [],
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
    }

    db.collection("notes").document(note_id).set(record)

    return {
        "status": "created",
        "note": _serialize(record),
    }


def append_note(
    *,
    related_entity: str,
    related_id: str,
    body: str,
    note_type: str = "activity_note",
    author: str = "ResolveX System",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience method for adding short timeline-style notes.
    """
    preview = body[:60].strip()
    if len(body) > 60:
        preview += "..."

    return create_note(
        title=preview or "Activity note",
        note_type=note_type,
        related_entity=related_entity,
        related_id=related_id,
        body=body,
        author=author,
        tags=tags,
        metadata=metadata,
    )


def update_note(note_id: str, body: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Updates an existing note.
    """
    note_ref = db.collection("notes").document(note_id)
    note_doc = note_ref.get()

    if not note_doc.exists:
        return {
            "status": "not_found",
            "note_id": note_id,
            "message": "Note not found.",
        }

    payload = {
        "body": body,
        "updated_at": _utc_now(),
    }

    if tags is not None:
        payload["tags"] = tags

    note_ref.update(payload)

    updated = note_ref.get().to_dict()

    return {
        "status": "updated",
        "note": _serialize(updated),
    }


def get_note(note_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns one note by ID.
    """
    doc = db.collection("notes").document(note_id).get()
    if not doc.exists:
        return None
    return _serialize(doc.to_dict())


def get_notes_by_entity(
    related_entity: str,
    related_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Returns notes for a given entity.
    """
    docs = (
        db.collection("notes")
        .where("related_entity", "==", related_entity)
        .where("related_id", "==", related_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_recent_notes(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns recent notes for activity feeds / dashboards.
    """
    docs = (
        db.collection("notes")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_notes_summary(limit: int = 200) -> Dict[str, Any]:
    """
    Returns counts by note type for dashboard overview.
    """
    notes = get_recent_notes(limit=limit)

    summary: Dict[str, int] = {
        "total_notes": len(notes),
    }

    for note in notes:
        note_type = note.get("note_type", "unknown")
        summary[note_type] = summary.get(note_type, 0) + 1

    return summary


if __name__ == "__main__":
    result = create_note(
        title="Initial complaint logged",
        note_type="complaint_log",
        related_entity="complaint",
        related_id="demo-complaint-001",
        body="Customer reported that the Voltix Charger overheats after 5 minutes of use.",
        author="ResolveX Listener Agent",
        tags=["complaint", "defect", "high_priority"],
        metadata={
            "product_name": "Voltix Charger",
            "issue_type": "defect",
        },
    )

    print("Created Note:")
    print(result)