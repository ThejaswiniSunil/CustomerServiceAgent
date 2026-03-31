import os
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

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LEARNING_TRIGGER_INTERVAL = int(os.getenv("LEARNING_TRIGGER_INTERVAL", "10"))

db = firestore.Client(project=PROJECT_ID)


class ResolveXOrchestrator:
    """
    Central workflow controller for ResolveX.
    Coordinates all agents to process a complaint end-to-end.
    """

    def handle_complaint(self, complaint_text: str) -> Dict[str, Any]:
        """
        Main complaint handling pipeline.
        """
        result: Dict[str, Any] = {
            "complaint_text": complaint_text,
            "steps": {},
            "complaint_id": None,
            "customer_response": {},
        }

        # Step 1: Listener Agent
        print("[ResolveX] Step 1: Listening to complaint...")
        listener_result = listen(complaint_text)
        result["steps"]["listener"] = listener_result
        extracted_data = listener_result.get("extracted_data", {})

        # Step 2: Analyst Agent
        print("[ResolveX] Step 2: Analyzing eligibility...")
        eligibility = check_eligibility(extracted_data)
        result["steps"]["analyst"] = eligibility

        # Step 3: Decision Agent
        print("[ResolveX] Step 3: Making decision...")
        decision = decide(extracted_data, eligibility)
        result["steps"]["decision"] = decision

        # Step 4: Database Agent
        print("[ResolveX] Step 4: Logging complaint...")
        logged = log_complaint(extracted_data, eligibility, decision)
        result["steps"]["database"] = logged
        result["complaint_id"] = logged.get("complaint_id")

        # Step 5: Insight Agent
        print("[ResolveX] Step 5: Detecting patterns...")
        product_name = extracted_data.get("product_name", "Unknown")
        insight = analyze(product_name)
        result["steps"]["insight"] = insight

        # Step 6: Manufacturer Agent
        if insight.get("pattern_detected"):
            print("[ResolveX] Step 6: Pattern detected, contacting manufacturer...")
            manufacturer_result = contact_manufacturer(insight)
            result["steps"]["manufacturer"] = manufacturer_result
        else:
            print("[ResolveX] Step 6: No manufacturer action needed yet.")
            result["steps"]["manufacturer"] = {
                "status": "monitoring",
                "product_name": product_name,
                "message": (
                    f"Monitoring {product_name}: "
                    f"{insight.get('total_complaints', 0)}/"
                    f"{insight.get('threshold', 3)} complaints before escalation."
                ),
            }

        # Step 7: Learning Agent
        complaint_count = self._increment_complaint_count()
        if complaint_count % LEARNING_TRIGGER_INTERVAL == 0:
            print(f"[ResolveX] Step 7: Running learning agent at complaint #{complaint_count}...")
            learning_result = improve()
            result["steps"]["learning"] = learning_result
        else:
            result["steps"]["learning"] = {
                "status": "skipped",
                "current_complaint_count": complaint_count,
                "next_learning_in": LEARNING_TRIGGER_INTERVAL - (complaint_count % LEARNING_TRIGGER_INTERVAL),
            }

        # Final customer-facing summary
        result["customer_response"] = {
            "acknowledgement": listener_result.get("customer_message"),
            "resolution": decision.get("customer_message"),
            "complaint_id": result["complaint_id"],
            "decision": decision.get("decision"),
            "estimated_resolution_days": decision.get("estimated_resolution_days"),
        }

        print(f"[ResolveX] Complaint handled successfully. ID: {result['complaint_id']}")
        return result

    def run_tracker(self, product_name: str) -> Dict[str, Any]:
        """
        Manually trigger tracker follow-up for a product.
        """
        return track_and_followup(product_name)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Returns structured dashboard data for frontend consumption.
        """
        complaints: List[Dict[str, Any]] = get_all_complaints()
        product_stats: List[Dict[str, Any]] = get_product_stats()

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

        manufacturer_cases = [
            p for p in product_stats if p.get("manufacturer_contacted", False)
        ]

        return {
            "summary": {
                "total_complaints": total_complaints,
                "total_products_flagged": len(product_stats),
                "manufacturer_cases": len(manufacturer_cases),
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
        """
        counter_ref = db.collection("system").document("stats")
        counter_doc = counter_ref.get()

        if counter_doc.exists:
            current_count = counter_doc.to_dict().get("complaint_count", 0)
            new_count = current_count + 1
            counter_ref.update({"complaint_count": new_count})
            return new_count

        counter_ref.set({"complaint_count": 1})
        return 1


# Singleton instance
orchestrator = ResolveXOrchestrator()