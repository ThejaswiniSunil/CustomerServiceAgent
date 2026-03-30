"""
mcp/calendar_tool.py
─────────────────────
Google Calendar MCP tool for ResolveX.

Used by the tracker_agent to schedule follow-up reminders
when the manufacturer has not responded within the expected window.
"""

import os
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

# Default: remind again after this many days if no response
DEFAULT_FOLLOWUP_DAYS = int(os.getenv("FOLLOWUP_REMINDER_DAYS", "3"))


def add_followup_reminder(
    product_name: str,
    reason: str,
    remind_in_days: int = DEFAULT_FOLLOWUP_DAYS
) -> dict:
    """
    Schedules a follow-up reminder for a manufacturer contact.

    Stores the reminder in Firestore under `calendar_reminders/{product_name}`.
    In production, this would also create a Google Calendar event via the
    Calendar API using the service account credentials.

    Args:
        product_name: The product with a pending manufacturer response.
        reason: Short description of why the reminder is needed.
        remind_in_days: How many days from now to schedule the reminder.

    Returns:
        dict with status, reminder_id, and scheduled_at timestamp.
    """

    remind_at = datetime.now(timezone.utc) + timedelta(days=remind_in_days)

    reminder = {
        "product_name": product_name,
        "reason": reason,
        "remind_at": remind_at,
        "remind_in_days": remind_in_days,
        "is_done": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Upsert — one active reminder per product at a time
    db.collection("calendar_reminders").document(product_name).set(reminder)

    # ── Optional: Google Calendar API integration ──────────────
    # Uncomment and configure once Google Calendar credentials are set up.
    #
    # from googleapiclient.discovery import build
    # from google.oauth2 import service_account
    #
    # SCOPES = ["https://www.googleapis.com/auth/calendar"]
    # SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    # creds = service_account.Credentials.from_service_account_file(
    #     SERVICE_ACCOUNT_FILE, scopes=SCOPES
    # )
    # service = build("calendar", "v3", credentials=creds)
    #
    # event = {
    #     "summary": f"ResolveX Follow-up: {product_name}",
    #     "description": reason,
    #     "start": {"dateTime": remind_at.isoformat(), "timeZone": "UTC"},
    #     "end": {
    #         "dateTime": (remind_at + timedelta(minutes=30)).isoformat(),
    #         "timeZone": "UTC"
    #     },
    # }
    # service.events().insert(calendarId="primary", body=event).execute()
    # ──────────────────────────────────────────────────────────

    return {
        "status": "reminder_set",
        "product_name": product_name,
        "remind_at": remind_at.isoformat(),
        "reason": reason,
    }


def list_upcoming_reminders(within_days: int = 7) -> list:
    """
    Returns all pending reminders due within the next N days.

    Args:
        within_days: Look-ahead window in days (default 7).

    Returns:
        List of reminder dicts ordered by remind_at ascending.
    """

    cutoff = datetime.now(timezone.utc) + timedelta(days=within_days)

    docs = (
        db.collection("calendar_reminders")
        .where("is_done", "==", False)
        .where("remind_at", "<=", cutoff)
        .order_by("remind_at")
        .stream()
    )

    return [doc.to_dict() for doc in docs]


def mark_reminder_done(product_name: str) -> dict:
    """
    Marks a reminder as completed once the follow-up action is taken.

    Args:
        product_name: The product whose reminder should be dismissed.

    Returns:
        dict with status confirmation.
    """

    db.collection("calendar_reminders").document(product_name).update({
        "is_done": True,
        "completed_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    return {
        "status": "reminder_completed",
        "product_name": product_name,
    }