import os
from google.cloud import firestore
from dotenv import load_dotenv

from agents.listener_agent import listen
from agents.analyst_agent import check_eligibility
from agents.decision_agent import decide
from agents.database_agent import log_complaint, get_all_complaints, get_product_stats
from agents.insight_agent import analyze
from agents.manufacturer_agent import contact_manufacturer
from agents.tracker_agent import track_and_followup
from agents.learning_agent import improve

load_dotenv()

db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

# Counter for triggering learning agent
complaint_counter_key = "system_complaint_count"
LEARNING_TRIGGER_INTERVAL = int(os.getenv("LEARNING_TRIGGER_INTERVAL", "10"))


class ResolveXOrchestrator:

    def handle_complaint(self, complaint_text: str) -> dict:
        """
        Main entry point. Coordinates all agents to handle
        a customer complaint end to end.
        """

        result = {
            "complaint_text": complaint_text,
            "steps": {}
        }

        # ── Step 1: Listener Agent ──────────────────────────────
        print("[ResolveX] Step 1: Listening to complaint...")
        listener_result = listen(complaint_text)
        result["steps"]["listener"] = listener_result
        extracted_data = listener_result["extracted_data"]

        # ── Step 2: Analyst Agent ──────────────────────────────
        print("[ResolveX] Step 2: Analysing eligibility...")
        eligibility = check_eligibility(extracted_data)
        result["steps"]["analyst"] = eligibility

        # ── Step 3: Decision Agent ─────────────────────────────
        print("[ResolveX] Step 3: Making decision...")
        decision = decide(extracted_data, eligibility)
        result["steps"]["decision"] = decision

        # ── Step 4: Database Agent ─────────────────────────────
        print("[ResolveX] Step 4: Logging to database...")
        logged = log_complaint(extracted_data, eligibility, decision)
        result["steps"]["database"] = logged
        result["complaint_id"] = logged["complaint_id"]

        # ── Step 5: Insight Agent ──────────────────────────────
        print("[ResolveX] Step 5: Analysing patterns...")
        product_name = extracted_data.get("product_name", "Unknown")
        insight = analyze(product_name)
        result["steps"]["insight"] = insight

        # ── Step 6: Manufacturer Agent (if pattern detected) ───
        if insight.get("pattern_detected"):
            print("[ResolveX] Step 6: Pattern detected — contacting manufacturer...")
            manufacturer_result = contact_manufacturer(insight)
            result["steps"]["manufacturer"] = manufacturer_result
        else:
            print("[ResolveX] Step 6: No pattern detected yet — monitoring...")
            result["steps"]["manufacturer"] = {
                "status": "monitoring",
                "message": f"Monitoring {product_name} — "
                           f"{insight.get('total_complaints', 0)}/"
                           f"{insight.get('threshold', 3)} complaints"
            }

        # ── Step 7: Learning Agent (every N complaints) ────────
        complaint_count = self._increment_complaint_count()
        if complaint_count % LEARNING_TRIGGER_INTERVAL == 0:
            print(f"[ResolveX] Step 7: Running learning agent "
                  f"(complaint #{complaint_count})...")
            learning_result = improve()
            result["steps"]["learning"] = learning_result
        else:
            result["steps"]["learning"] = {
                "status": "skipped",
                "next_learning_at": (
                    LEARNING_TRIGGER_INTERVAL
                    - (complaint_count % LEARNING_TRIGGER_INTERVAL)
                )
            }

        # ── Final: Build customer-facing response ──────────────
        result["customer_response"] = {
            "acknowledgement": listener_result.get("customer_message"),
            "resolution": decision.get("customer_message"),
            "complaint_id": logged["complaint_id"],
            "decision": decision.get("decision"),
            "estimated_resolution_days": decision.get("estimated_resolution_days")
        }

        print(f"[ResolveX] Complaint handled. ID: {logged['complaint_id']}")
        return result

    def run_tracker(self, product_name: str) -> dict:
        """Manually trigger tracker for a specific product."""
        return track_and_followup(product_name)

    def get_dashboard_data(self) -> dict:
        """Returns all data needed for the dashboard."""
        complaints = get_all_complaints()
        product_stats = get_product_stats()

        total = len(complaints)
        resolutions = {}
        for c in complaints:
            res = c.get("resolution", "unknown")
            resolutions[res] = resolutions.get(res, 0) + 1

        return {
            "total_complaints": total,
            "resolution_breakdown": resolutions,
            "product_stats": product_stats,
            "recent_complaints": complaints[:10]
        }

    def _increment_complaint_count(self) -> int:
        """Increments and returns the global complaint counter."""
        counter_ref = db.collection("system").document("stats")
        counter_doc = counter_ref.get()

        if counter_doc.exists:
            count = counter_doc.to_dict().get("complaint_count", 0) + 1
            counter_ref.update({"complaint_count": count})
        else:
            count = 1
            counter_ref.set({"complaint_count": count})

        return count


# Singleton instance
orchestrator = ResolveXOrchestrator()