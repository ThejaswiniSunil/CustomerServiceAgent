"""
database/schema.py
──────────────────
Firestore schema definitions and helper models for ResolveX.

Collections
───────────
  complaints             – one doc per customer complaint
  product_stats          – one doc per product (aggregated stats)
  manufacturer_contacts  – one doc per product contacted
  system/stats           – global counters

All timestamps are UTC datetime objects (firestore auto-serialises them).
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Complaint ─────────────────────────────────────────────────────────────────

@dataclass
class ComplaintSchema:
    """
    Firestore path: complaints/{complaint_id}

    Created by: database_agent.log_complaint()
    """

    # Identity
    complaint_id: str = ""
    timestamp: datetime = field(default_factory=_now)

    # Product
    product_name: str = "Unknown"
    order_id: str = "Not provided"

    # Complaint details (from listener_agent)
    issue_type: str = "other"          # defective | wrong_item | damaged | late | other
    complaint_summary: str = ""
    urgency_level: str = "medium"      # low | medium | high
    customer_emotion: str = "neutral"  # frustrated | angry | neutral | sad

    # Eligibility (from analyst_agent)
    days_since_purchase: Optional[int] = None
    policy_applied: str = ""

    # Decision (from decision_agent)
    resolution: str = "escalate"       # refund | replacement | repair | escalate | goodwill
    decision_reason: str = ""
    priority: str = "medium"
    estimated_resolution_days: int = 3

    # Tracking flags
    manufacturer_contacted: bool = False
    manufacturer_resolved: bool = False
    customer_notified_of_fix: bool = False
    closing_message: str = ""
    loop_closed_at: Optional[datetime] = None
    is_resolved: bool = True

    # Metadata
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Product Stats ─────────────────────────────────────────────────────────────

@dataclass
class ProductStatsSchema:
    """
    Firestore path: product_stats/{product_name}

    Created/updated by: database_agent.update_product_stats()
    """

    product_name: str = "Unknown"
    total_complaints: int = 0
    issue_counts: dict = field(default_factory=dict)   # {issue_type: count}
    complaint_ids: list = field(default_factory=list)

    # Manufacturer flags
    manufacturer_contacted: bool = False
    manufacturer_resolved: bool = False
    manufacturer_contacted_at: Optional[datetime] = None
    manufacturer_resolved_at: Optional[datetime] = None

    first_complaint_at: datetime = field(default_factory=_now)
    last_complaint_at: datetime = field(default_factory=_now)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Manufacturer Contact ───────────────────────────────────────────────────────

@dataclass
class ManufacturerContactSchema:
    """
    Firestore path: manufacturer_contacts/{product_name}

    Created by: manufacturer_agent.contact_manufacturer()
    Updated by: tracker_agent.track_and_followup() / mark_resolved()
    """

    product_name: str = ""
    total_complaints: int = 0
    severity_level: str = "high"       # medium | high | critical
    email_subject: str = ""
    email_body: str = ""

    # Follow-up tracking
    follow_up_count: int = 0
    last_followup_at: Optional[datetime] = None
    last_followup_body: str = ""

    # Status flags
    issue_resolved: bool = False
    escalated: bool = False

    contacted_at: datetime = field(default_factory=_now)
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── System Stats ──────────────────────────────────────────────────────────────

@dataclass
class SystemStatsSchema:
    """
    Firestore path: system/stats

    Used by orchestrator to track global complaint count for
    triggering the learning agent.
    """
    complaint_count: int = 0
    last_learning_run_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Field constants (avoids magic strings across the codebase) ─────────────────

class Fields:
    """Shared Firestore field name constants."""

    # complaints
    COMPLAINT_ID = "complaint_id"
    PRODUCT_NAME = "product_name"
    ORDER_ID = "order_id"
    ISSUE_TYPE = "issue_type"
    COMPLAINT_SUMMARY = "complaint_summary"
    URGENCY_LEVEL = "urgency_level"
    CUSTOMER_EMOTION = "customer_emotion"
    RESOLUTION = "resolution"
    PRIORITY = "priority"
    ESTIMATED_RESOLUTION_DAYS = "estimated_resolution_days"
    MANUFACTURER_CONTACTED = "manufacturer_contacted"
    MANUFACTURER_RESOLVED = "manufacturer_resolved"
    CUSTOMER_NOTIFIED_OF_FIX = "customer_notified_of_fix"
    IS_RESOLVED = "is_resolved"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    # product_stats
    TOTAL_COMPLAINTS = "total_complaints"
    ISSUE_COUNTS = "issue_counts"
    COMPLAINT_IDS = "complaint_ids"

    # manufacturer_contacts
    FOLLOW_UP_COUNT = "follow_up_count"
    ISSUE_RESOLVED = "issue_resolved"
    ESCALATED = "escalated"
    SEVERITY_LEVEL = "severity_level"

    # system/stats
    COMPLAINT_COUNT = "complaint_count"


# ── Collection names ──────────────────────────────────────────────────────────

class Collections:
    COMPLAINTS = "complaints"
    PRODUCT_STATS = "product_stats"
    MANUFACTURER_CONTACTS = "manufacturer_contacts"
    SYSTEM = "system"