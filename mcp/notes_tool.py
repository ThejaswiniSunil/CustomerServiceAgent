"""
mcp/notes_tool.py
──────────────────
Internal notes MCP tool for ResolveX.

Allows agents to persist structured notes about products, complaints,
and resolutions. Used by the learning_agent to store improvement
insights for future reference.
"""

import os
from datetime import datetime, timezone
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))


def save_note(
    title: str,
    content: str,
    product_name: str = None,
    note_type: str = "general",
    tags: list = None,
) -> dict:
    """
    Saves a structured note to Firestore.

    Args:
        title: Short title for the note.
        content: Full note body (can be AI-generated insights).
        product_name: Optional — links the note to a specific product.
        note_type: One of 'general' | 'insight' | 'learning' | 'alert'.
        tags: Optional list of string tags for filtering.

    Returns:
        dict with note_id and status.
    """

    note_id = f"note_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    now = datetime.now(timezone.utc)

    note = {
        "note_id": note_id,
        "title": title,
        "content": content,
        "product_name": product_name,
        "note_type": note_type,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }

    db.collection("notes").document(note_id).set(note)

    return {
        "status": "note_saved",
        "note_id": note_id,
        "title": title,
        "note_type": note_type,
    }


def get_notes_for_product(product_name: str, note_type: str = None) -> list:
    """
    Retrieves all notes linked to a specific product.

    Args:
        product_name: The product to filter notes by.
        note_type: Optional filter by note type.

    Returns:
        List of note dicts ordered by newest first.
    """

    query = (
        db.collection("notes")
        .where("product_name", "==", product_name)
    )

    if note_type:
        query = query.where("note_type", "==", note_type)

    docs = query.order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).stream()

    return [doc.to_dict() for doc in docs]


def get_notes_by_type(note_type: str, limit: int = 20) -> list:
    """
    Retrieves notes filtered by type. Useful for the learning_agent
    to pull all 'learning' or 'insight' notes.

    Args:
        note_type: e.g. 'learning' | 'insight' | 'alert'
        limit: Max number of results to return.

    Returns:
        List of note dicts ordered by newest first.
    """

    docs = (
        db.collection("notes")
        .where("note_type", "==", note_type)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [doc.to_dict() for doc in docs]


def delete_note(note_id: str) -> dict:
    """
    Deletes a note by its ID.

    Args:
        note_id: The Firestore document ID of the note.

    Returns:
        dict with status confirmation.
    """

    db.collection("notes").document(note_id).delete()

    return {
        "status": "note_deleted",
        "note_id": note_id,
    }