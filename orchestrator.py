import os
import logging
from typing import Any, Dict, List

from google.cloud import firestore
from dotenv import load_dotenv

from agents.listener_agent import listen
from agents.analyst_agent import check_eligibility
from agents.decision_agent import decide
from agents.database_agent import (
    log_complaint,
    get_all_complaints,
    get_product_stats,
)
from agents.insight_agent import analyze
from agents.manufacturer_agent import contact_manufacturer
from agents.tracker_agent import track_and_followup
from agents.learning_agent import improve

# MCP tool — task management
from mcp.task_tool import create_task

load_dotenv()

# Setup logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Safe env var parsing
try:
    LEARNING_TRIGGER_INTERVAL = int(os.getenv("LEARNING_TRIGGER_INTERVAL", "10"))
except ValueError:
    LEARNING_TRIGGER_INTERVAL = 10
    logger.warning("[orchestrator] LEARNING_TRIGGER_INTERVAL invalid — defaulting to 10")

db = firestore.Client(project=PROJECT_ID)


class ResolveXOrchestrator:
    """
    Central workflow controller for ResolveX.
    Coordinates all agents to process a complaint end-to-end.
    Each step is independently protected — one agent failing
    never crashes the entire pipeline.

    MCP tools connected:
      - task_tool: creates a Firestore task when decision = escalate
    """

    def handle_complaint(self, complaint_text: str) -> Dict[str, Any]:
        """
        Main complaint handling pipeline.
        Each agent step is wrapped independently so partial
        failures are logged and recovered gracefully.
        """
        result: Dict[str, Any] = {
            "complaint_text": complaint_text,
            "steps": {},
            "complaint_id": None,
            "customer_response": {},
        }

        # ── Step 1: Listener Agent ────────────────────────────
        logger.info("[orchestrator] Step 1: Listener Agent")
        extracted_data = {}
        listener_result = {}
        try:
            listener_result = listen(complaint_text)
            result["steps"]["listener"] = listener_result
            extracted_data = listener_result.get("extracted_data", {})
            logger.info(f"[orchestrator] Listener complete: {extracted_data.get('product_name')}")
        except Exception as e:
            logger.error(f"[orchestrator] Listener Agent failed: {e}")
            result["steps"]["listener"] = {"status": "error", "error": str(e)}
            result["customer_response"] = {
                "acknowledgement": "We received your complaint and are reviewing it.",
                "resolution": "Our team will be in touch shortly.",
                "complaint_id": None,
                "decision": "escalate",
                "estimated_resolution_days": 3
            }
            return result

        # ── Step 2: Analyst Agent ────────────────────────────
        logger.info("[orchestrator] Step 2: Analyst Agent")
        eligibility = {}
        try:
            eligibility = check_eligibility(extracted_data)
            result["steps"]["analyst"] = eligibility
            logger.info(f"[orchestrator] Analyst complete: {eligibility.get('eligible_for')}")
        except Exception as e:
            logger.error(f"[orchestrator] Analyst Agent failed: {e}")
            result["steps"]["analyst"] = {"status": "error", "error": str(e)}
            eligibility = {
                "eligible_for": "escalate",
                "reason": "Could not determine eligibility automatically"
            }

        # ── Step 3: Decision Agent ───────────────────────────
        logger.info("[orchestrator] Step 3: Decision Agent")
        decision = {}
        try:
            decision = decide(extracted_data, eligibility)
            result["steps"]["decision"] = decision
            logger.info(f"[orchestrator] Decision complete: {decision.get('decision')}")
        except Exception as e:
            logger.error(f"[orchestrator] Decision Agent failed: {e}")
            result["steps"]["decision"] = {"status": "error", "error": str(e)}
            decision = {
                "decision": "escalate",
                "customer_message": (
                    "We have received your complaint and our team will "
                    "review it manually within 24 hours."
                ),
                "estimated_resolution_days": 3,
                "priority": "high"
            }

        # ── Step 4: Database Agent ───────────────────────────
        logger.info("[orchestrator] Step 4: Database Agent")
        logged = {}
        try:
            logged = log_complaint(extracted_data, eligibility, decision)
            result["steps"]["database"] = logged
            result["complaint_id"] = logged.get("complaint_id")
            logger.info(f"[orchestrator] Logged complaint: {result['complaint_id']}")
        except Exception as e:
            logger.error(f"[orchestrator] Database Agent failed: {e}")
            result["steps"]["database"] = {"status": "error", "error": str(e)}

        # ── MCP Step: Task Tool ──────────────────────────────
        # If decision is escalate, create a task in Firestore via MCP task_tool
        # so the support team has a structured action item to follow up on.
        if decision.get("decision") == "escalate":
            logger.info("[orchestrator] MCP task_tool: creating escalation task")
            try:
                task = create_task(
                    title=f"Manual review required: {extracted_data.get('product_name', 'Unknown')}",
                    description=(
                        f"Complaint ID: {result.get('complaint_id')}\n"
                        f"Issue: {extracted_data.get('complaint_summary', '')}\n"
                        f"Reason: {decision.get('decision_reason', '')}"
                    ),
                    assigned_to="support_team",
                    priority=decision.get("priority", "high"),
                    product_name=extracted_data.get("product_name"),
                    complaint_id=result.get("complaint_id"),
                    due_in_days=int(decision.get("estimated_resolution_days", 3))
                )
                result["steps"]["mcp_task"] = task
                logger.info(f"[orchestrator] MCP task created: {task.get('task_id')}")
            except Exception as e:
                logger.error(f"[orchestrator] MCP task_tool failed: {e}")
                result["steps"]["mcp_task"] = {"status": "error", "error": str(e)}
        else:
            result["steps"]["mcp_task"] = {
                "status": "skipped",
                "reason": f"Decision was {decision.get('decision')} — no manual task needed"
            }

        # ── Step 5: Insight Agent ────────────────────────────
        logger.info("[orchestrator] Step 5: Insight Agent")
        insight = {}
        product_name = extracted_data.get("product_name", "Unknown")
        try:
            insight = analyze(product_name)
            result["steps"]["insight"] = insight
            logger.info(
                f"[orchestrator] Insight complete: "
                f"pattern_detected={insight.get('pattern_detected')}"
            )
        except Exception as e:
            logger.error(f"[orchestrator] Insight Agent failed: {e}")
            result["steps"]["insight"] = {"status": "error", "error": str(e)}

        # ── Step 6: Manufacturer Agent ───────────────────────
        if insight.get("pattern_detected"):
            logger.info("[orchestrator] Step 6: Manufacturer Agent — pattern detected")
            try:
                manufacturer_result = contact_manufacturer(insight)
                result["steps"]["manufacturer"] = manufacturer_result
                logger.info(
                    f"[orchestrator] Manufacturer contacted: "
                    f"{manufacturer_result.get('email_sent')}"
                )
            except Exception as e:
                logger.error(f"[orchestrator] Manufacturer Agent failed: {e}")
                result["steps"]["manufacturer"] = {"status": "error", "error": str(e)}
        else:
            total = insight.get("total_complaints", 0)
            threshold = insight.get("threshold", 3)
            logger.info(
                f"[orchestrator] Step 6: Monitoring — "
                f"{total}/{threshold} complaints for {product_name}"
            )
            result["steps"]["manufacturer"] = {
                "status": "monitoring",
                "product_name": product_name,
                "message": (
                    f"Monitoring {product_name}: "
                    f"{total}/{threshold} complaints before escalation."
                ),
            }

        # ── Step 7: Learning Agent ───────────────────────────
        complaint_count = self._increment_complaint_count()
        if complaint_count % LEARNING_TRIGGER_INTERVAL == 0:
            logger.info(
                f"[orchestrator] Step 7: Learning Agent triggered "
                f"at complaint #{complaint_count}"
            )
            try:
                learning_result = improve()
                result["steps"]["learning"] = learning_result
                logger.info("[orchestrator] Learning Agent complete")
            except Exception as e:
                logger.error(f"[orchestrator] Learning Agent failed: {e}")
                result["steps"]["learning"] = {"status": "error", "error": str(e)}
        else:
            remaining = LEARNING_TRIGGER_INTERVAL - (complaint_count % LEARNING_TRIGGER_INTERVAL)
            result["steps"]["learning"] = {
                "status": "skipped",
                "current_complaint_count": complaint_count,
                "next_learning_in": remaining,
            }

        # ── Final: Customer Response ─────────────────────────
        result["customer_response"] = {
            "acknowledgement": listener_result.get("customer_message",
                "Thank you for reaching out. We are reviewing your complaint."),
            "resolution": decision.get("customer_message",
                "Our team will be in touch with a resolution shortly."),
            "complaint_id": result["complaint_id"],
            "decision": decision.get("decision", "escalate"),
            "estimated_resolution_days": decision.get("estimated_resolution_days", 3),
        }

        logger.info(f"[orchestrator] Pipeline complete. ID: {result['complaint_id']}")
        return result

    def run_tracker(self, product_name: str) -> Dict[str, Any]:
        """Manually trigger tracker follow-up for a product."""
        logger.info(f"[orchestrator] Tracker triggered for: {product_name}")
        try:
            return track_and_followup(product_name)
        except Exception as e:
            logger.error(f"[orchestrator] Tracker failed: {e}")
            return {"status": "error", "product_name": product_name, "error": str(e)}

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Returns structured dashboard data for frontend consumption."""
        logger.info("[orchestrator] Building dashboard data")
        try:
            complaints: List[Dict[str, Any]] = get_all_complaints()
            product_stats: List[Dict[str, Any]] = get_product_stats()
        except Exception as e:
            logger.error(f"[orchestrator] Dashboard data fetch failed: {e}")
            return {
                "summary": {},
                "resolution_breakdown": {},
                "priority_breakdown": {},
                "issue_breakdown": {},
                "product_stats": [],
                "recent_complaints": [],
                "error": str(e)
            }

        total_complaints = len(complaints)
        resolution_breakdown: Dict[str, int] = {}
        priority_breakdown: Dict[str, int] = {}
        issue_breakdown: Dict[str, int] = {}

        for complaint in complaints:
            resolution = complaint.get("resolution", "unknown")
            priority = complaint.get("priority", "unknown")
            issue_type = complaint.get("issue_type", "unknown")
            resolution_breakdown[resolution] = resolution_breakdown.get(resolution, 0) + 1
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
            issue_breakdown[issue_type] = issue_breakdown.get(issue_type, 0) + 1

        manufacturer_contacted = [
            p for p in product_stats if p.get("manufacturer_contacted", False)
        ]
        manufacturer_resolved = [
            p for p in product_stats if p.get("manufacturer_resolved", False)
        ]

        return {
            "summary": {
                "total_complaints": total_complaints,
                "total_products_flagged": len(product_stats),
                "manufacturer_contacted": len(manufacturer_contacted),
                "manufacturer_resolved": len(manufacturer_resolved),
                "auto_resolve_rate": (
                    round((total_complaints / total_complaints) * 100, 1)
                    if total_complaints > 0 else 0
                ),
            },
            "resolution_breakdown": resolution_breakdown,
            "priority_breakdown": priority_breakdown,
            "issue_breakdown": issue_breakdown,
            "product_stats": product_stats,
            "recent_complaints": complaints[:10],
        }

    def _increment_complaint_count(self) -> int:
        """
        Increments and returns the system-wide complaint counter.
        Uses Firestore transactions to avoid race conditions.
        """
        counter_ref = db.collection("system").document("stats")

        try:
            transaction = db.transaction()

            @firestore.transactional
            def update_in_transaction(transaction, ref):
                snapshot = ref.get(transaction=transaction)
                if snapshot.exists:
                    new_count = snapshot.get("complaint_count") + 1
                else:
                    new_count = 1
                transaction.set(ref, {"complaint_count": new_count}, merge=True)
                return new_count

            return update_in_transaction(transaction, counter_ref)

        except Exception as e:
            logger.error(f"[orchestrator] Counter increment failed: {e}")
            try:
                doc = counter_ref.get()
                return doc.to_dict().get("complaint_count", 0) if doc.exists else 0
            except Exception:
                return 0


# Singleton instance
orchestrator = ResolveXOrchestrator()