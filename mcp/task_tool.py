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


def _build_due_date(priority: str) -> datetime:
    """
    Creates a due date based on priority.
    """
    now = _utc_now()

    priority = (priority or "medium").lower()

    if priority == "urgent":
        return now + timedelta(hours=12)
    if priority == "high":
        return now + timedelta(days=1)
    if priority == "medium":
        return now + timedelta(days=3)
    return now + timedelta(days=5)


def create_task(
    *,
    title: str,
    task_type: str,
    related_entity: str,
    related_id: str,
    priority: str = "medium",
    description: str = "",
    assigned_to: str = "ResolveX Ops",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a task record in Firestore.
    """
    task_id = str(uuid.uuid4())
    now = _utc_now()
    due_at = _build_due_date(priority)

    record = {
        "task_id": task_id,
        "title": title,
        "task_type": task_type,
        "description": description,
        "related_entity": related_entity,      # complaint / manufacturer / product
        "related_id": related_id,
        "priority": priority,
        "status": "open",                      # open / in_progress / blocked / completed / cancelled
        "assigned_to": assigned_to,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
        "due_at": due_at,
        "completed_at": None,
    }

    db.collection("tasks").document(task_id).set(record)

    return {
        "status": "created",
        "task": _serialize(record),
    }


def update_task_status(
    task_id: str,
    new_status: str,
    note: str = "",
) -> Dict[str, Any]:
    """
    Updates the status of a task.
    """
    task_ref = db.collection("tasks").document(task_id)
    task_doc = task_ref.get()

    if not task_doc.exists:
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "Task not found.",
        }

    allowed_statuses = {"open", "in_progress", "blocked", "completed", "cancelled"}
    if new_status not in allowed_statuses:
        return {
            "status": "invalid_status",
            "task_id": task_id,
            "message": f"Invalid task status: {new_status}",
        }

    now = _utc_now()
    update_payload = {
        "status": new_status,
        "updated_at": now,
    }

    if note:
        update_payload["latest_note"] = note

    if new_status == "completed":
        update_payload["completed_at"] = now

    task_ref.update(update_payload)

    updated_doc = task_ref.get().to_dict()

    return {
        "status": "updated",
        "task": _serialize(updated_doc),
    }


def add_task_note(task_id: str, note: str) -> Dict[str, Any]:
    """
    Adds an operational note to a task.
    """
    task_ref = db.collection("tasks").document(task_id)
    task_doc = task_ref.get()

    if not task_doc.exists:
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "Task not found.",
        }

    current = task_doc.to_dict()
    notes = current.get("notes", [])
    notes.append({
        "note": note,
        "created_at": _utc_now(),
    })

    task_ref.update({
        "notes": notes,
        "latest_note": note,
        "updated_at": _utc_now(),
    })

    updated_doc = task_ref.get().to_dict()

    return {
        "status": "note_added",
        "task": _serialize(updated_doc),
    }


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns one task by ID.
    """
    doc = db.collection("tasks").document(task_id).get()
    if not doc.exists:
        return None
    return _serialize(doc.to_dict())


def get_tasks(
    status: Optional[str] = None,
    related_entity: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Returns tasks with optional filtering.
    """
    query = db.collection("tasks")

    if status:
        query = query.where("status", "==", status)

    if related_entity:
        query = query.where("related_entity", "==", related_entity)

    docs = (
        query.order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [_serialize(doc.to_dict()) for doc in docs]


def get_open_task_summary() -> Dict[str, Any]:
    """
    Returns a lightweight summary of task operations.
    """
    tasks = get_tasks(limit=200)

    summary = {
        "total_tasks": len(tasks),
        "open": 0,
        "in_progress": 0,
        "blocked": 0,
        "completed": 0,
        "cancelled": 0,
        "urgent": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for task in tasks:
        status = task.get("status", "open")
        priority = task.get("priority", "medium")

        if status in summary:
            summary[status] += 1

        if priority in summary:
            summary[priority] += 1

    return summary


if __name__ == "__main__":
    created = create_task(
        title="Review recurring charger defect complaints",
        task_type="manufacturer_followup",
        related_entity="product",
        related_id="Voltix Charger",
        priority="high",
        description="Investigate repeated defect complaints and prepare escalation workflow.",
        metadata={
            "complaint_count": 4,
            "dominant_issue": "defect",
        },
    )

    print("Created Task:")
    print(created)