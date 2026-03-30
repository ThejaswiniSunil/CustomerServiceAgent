"""
mcp/task_tool.py
─────────────────
Task management MCP tool for ResolveX.

Allows agents to create, complete, and list operational tasks.
Used by the decision_agent (escalations), tracker_agent (follow-ups),
and manufacturer_agent (manufacturer actions).
"""

import os
from datetime import datetime, timezone
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

# Task priority levels
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_CRITICAL = "critical"

# Task status values
STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"


def create_task(
    title: str,
    description: str,
    assigned_to: str = "system",
    priority: str = PRIORITY_MEDIUM,
    product_name: str = None,
    complaint_id: str = None,
    due_in_days: int = None,
) -> dict:
    """
    Creates a new task in Firestore.

    Args:
        title: Short task title.
        description: Full task details.
        assigned_to: Agent or team responsible (e.g. 'tracker_agent', 'support_team').
        priority: 'low' | 'medium' | 'high' | 'critical'
        product_name: Optional — links task to a product.
        complaint_id: Optional — links task to a specific complaint.
        due_in_days: Optional — number of days until due date.

    Returns:
        dict with task_id and status.
    """

    from datetime import timedelta

    task_id = f"task_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    now = datetime.now(timezone.utc)

    due_at = None
    if due_in_days is not None:
        due_at = now + timedelta(days=due_in_days)

    task = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "assigned_to": assigned_to,
        "priority": priority,
        "status": STATUS_OPEN,
        "product_name": product_name,
        "complaint_id": complaint_id,
        "due_at": due_at,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
    }

    db.collection("tasks").document(task_id).set(task)

    return {
        "status": "task_created",
        "task_id": task_id,
        "title": title,
        "priority": priority,
        "assigned_to": assigned_to,
        "due_at": due_at.isoformat() if due_at else None,
    }


def complete_task(task_id: str, resolution_note: str = "") -> dict:
    """
    Marks a task as completed.

    Args:
        task_id: The Firestore document ID of the task.
        resolution_note: Optional note describing how the task was resolved.

    Returns:
        dict with status confirmation.
    """

    now = datetime.now(timezone.utc)

    db.collection("tasks").document(task_id).update({
        "status": STATUS_DONE,
        "completed_at": now,
        "resolution_note": resolution_note,
        "updated_at": now,
    })

    return {
        "status": "task_completed",
        "task_id": task_id,
        "completed_at": now.isoformat(),
    }


def list_open_tasks(
    assigned_to: str = None,
    priority: str = None,
    product_name: str = None,
    limit: int = 50,
) -> list:
    """
    Returns open tasks, with optional filters.

    Args:
        assigned_to: Filter by agent/team name.
        priority: Filter by priority level.
        product_name: Filter by product.
        limit: Max results to return.

    Returns:
        List of task dicts ordered by priority then created_at.
    """

    query = db.collection("tasks").where("status", "==", STATUS_OPEN)

    if assigned_to:
        query = query.where("assigned_to", "==", assigned_to)

    if priority:
        query = query.where("priority", "==", priority)

    if product_name:
        query = query.where("product_name", "==", product_name)

    docs = query.order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).limit(limit).stream()

    return [doc.to_dict() for doc in docs]


def update_task_status(task_id: str, new_status: str) -> dict:
    """
    Updates the status of a task.

    Args:
        task_id: The task to update.
        new_status: 'open' | 'in_progress' | 'done' | 'cancelled'

    Returns:
        dict with status confirmation.
    """

    db.collection("tasks").document(task_id).update({
        "status": new_status,
        "updated_at": datetime.now(timezone.utc),
    })

    return {
        "status": "task_updated",
        "task_id": task_id,
        "new_status": new_status,
    }