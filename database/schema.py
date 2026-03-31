"""
database/schema.py
──────────────────
Firestore schema definitions and helper models for ResolveX.

Collections
───────────
  complaints             – one doc per customer complaint
  product_stats          – one doc per product (aggregated stats)
  manufacturer_contacts  – one doc per product contacted
  manufacturers          – manufacturer contact directory
  purchases              – customer purchase history
  learning_reports       – auto-generated learning insights
  system/stats           – global counters

All timestamps are UTC datetime objects (Firestore auto-serialises them).
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
    Updated by: tracker_agent.notify_customers()
    """

    # Identity
    complaint_id: str = ""
    timestamp: datetime = field(default_factory=_now)

    # Product
    product_name: str = "Unknown"
    order_id: str = "Not provided"

    # Complaint details (from listener_agent)
    # issue_type values: defect | damaged | wrong_item | not_as_described | missing_parts | other
    issue_type: str = "other"
    complaint_summary: str = ""
    urgency_level: str = "medium"       # low | medium | high
    customer_emotion: str = "neutral"   # frustrated | angry | disappointed | neutral | upset

    # Eligibility (from analyst_agent)
    days_since_purchase: Optional[int] = None
    policy_applied: str = ""

    # Decision (from decision_agent)
    resolution: str = "escalate"        # full_refund | replacement | partial_refund | escalate
    decision_reason: str = ""
    priority: str = "medium"            # low | medium | high | urgent
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

    Note: complaint_ids is capped at 500 entries to avoid
    hitting Firestore's 1MB document size limit.
    """

    product_name: str = "Unknown"
    total_complaints: int = 0
    issue_counts: dict = field(default_factory=dict)    # {issue_type: count}
    complaint_ids: list = field(default_factory=list)   # capped at 500

    # Pattern detection
    pattern_detected: bool = False
    pattern_detected_at: Optional[datetime] = None
    pattern_report: dict = field(default_factory=dict)

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
    manufacturer_email: str = ""        # ← added missing field
    total_complaints: int = 0
    severity_level: str = "high"        # medium | high | critical
    email_subject: str = ""
    email_body: str = ""

    # Email status
    email_sent: bool = False
    email_error: Optional[str] = None

    # Follow-up tracking
    follow_up_count: int = 0
    last_followup_at: Optional[datetime] = None
    last_followup_body: str = ""

    # Status flags
    response_received: bool = False
    issue_resolved: bool = False
    escalated: bool = False

    contacted_at: datetime = field(default_factory=_now)
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Manufacturer Directory ────────────────────────────────────────────────────

@dataclass
class ManufacturerSchema:
    """
    Firestore path: manufacturers/{product_name}

    Manually populated — stores manufacturer contact info.
    Used by: manufacturer_agent.get_manufacturer_email()
    """

    product_name: str = ""
    manufacturer_name: str = ""
    email: str = ""
    phone: str = ""
    country: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Purchase Record ───────────────────────────────────────────────────────────

@dataclass
class PurchaseSchema:
    """
    Firestore path: purchases/{order_id}

    Used by: analyst_agent.check_eligibility()
    Pre-populated with customer purchase data.
    """

    order_id: str = ""
    customer_id: str = ""
    product_name: str = ""
    model_number: str = ""
    purchase_date: datetime = field(default_factory=_now)
    price: float = 0.0
    warranty_months: int = 12
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Learning Report ───────────────────────────────────────────────────────────

@dataclass
class LearningReportSchema:
    """
    Firestore path: learning_reports/{auto_id}

    Created by: learning_agent.improve()
    """

    complaints_analyzed: int = 0
    most_common_issue: str = ""
    most_common_resolution: str = ""
    pattern_insights: list = field(default_factory=list)
    recommended_policy_updates: list = field(default_factory=list)
    improvement_summary: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── System Stats ──────────────────────────────────────────────────────────────

@dataclass
class SystemStatsSchema:
    """
    Firestore path: system/stats

    Used by orchestrator to track global complaint count
    for triggering the learning agent.
    """

    complaint_count: int = 0
    last_learning_run_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Field Constants ───────────────────────────────────────────────────────────

class Fields:
    """
    Shared Firestore field name constants.
    Use these instead of magic strings across the codebase.
    """

    # complaints
    COMPLAINT_ID = "complaint_id"
    PRODUCT_NAME = "product_name"
    ORDER_ID = "order_id"
    ISSUE_TYPE = "issue_type"
    COMPLAINT_SUMMARY = "complaint_summary"
    URGENCY_LEVEL = "urgency_level"
    CUSTOMER_EMOTION = "customer_emotion"
    DAYS_SINCE_PURCHASE = "days_since_purchase"
    POLICY_APPLIED = "policy_applied"
    RESOLUTION = "resolution"
    DECISION_REASON = "decision_reason"
    PRIORITY = "priority"
    ESTIMATED_RESOLUTION_DAYS = "estimated_resolution_days"
    MANUFACTURER_CONTACTED = "manufacturer_contacted"
    MANUFACTURER_RESOLVED = "manufacturer_resolved"
    CUSTOMER_NOTIFIED_OF_FIX = "customer_notified_of_fix"
    CLOSING_MESSAGE = "closing_message"
    LOOP_CLOSED_AT = "loop_closed_at"
    IS_RESOLVED = "is_resolved"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    # product_stats
    TOTAL_COMPLAINTS = "total_complaints"
    ISSUE_COUNTS = "issue_counts"
    COMPLAINT_IDS = "complaint_ids"
    PATTERN_DETECTED = "pattern_detected"

    # manufacturer_contacts
    MANUFACTURER_EMAIL = "manufacturer_email"
    EMAIL_SENT = "email_sent"
    FOLLOW_UP_COUNT = "follow_up_count"
    ISSUE_RESOLVED = "issue_resolved"
    ESCALATED = "escalated"
    SEVERITY_LEVEL = "severity_level"
    RESPONSE_RECEIVED = "response_received"

    # system/stats
    COMPLAINT_COUNT = "complaint_count"
    LAST_LEARNING_RUN_AT = "last_learning_run_at"


# ── Collection Names ──────────────────────────────────────────────────────────

class Collections:
    """
    All Firestore collection names used across ResolveX.
    Use these constants instead of hardcoded strings.
    """

    COMPLAINTS = "complaints"
    PRODUCT_STATS = "product_stats"
    MANUFACTURER_CONTACTS = "manufacturer_contacts"
    MANUFACTURERS = "manufacturers"
    PURCHASES = "purchases"
    LEARNING_REPORTS = "learning_reports"
    SYSTEM = "system"