import os
import json
import logging
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# MCP tool — notes storage
# Uses create_note() from mcp/notes_tool.py
from mcp.notes_tool import create_note

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_project = os.getenv("GOOGLE_CLOUD_PROJECT")
_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not _project:
    logger.warning("GOOGLE_CLOUD_PROJECT not set — Vertex AI will not initialize")
else:
    vertexai.init(project=_project, location=_location)

model = GenerativeModel("gemini-2.5-flash")
db = firestore.Client(project=_project)


def improve() -> dict:
    """
    Analyzes resolved complaints to find patterns and suggest policy updates.
    Saves insights as a structured note via MCP notes_tool.

    MCP tools used:
      - notes_tool.create_note: persists the learning summary as a searchable
        note so future agents and dashboards can retrieve insights without
        querying the learning_reports collection directly.

    IMPORTANT — Firestore composite index required:
      Collection: complaints | Fields: is_resolved ASC, created_at DESC
      gcloud firestore indexes composite create \
        --collection-group=complaints \
        --field-config=field-path=is_resolved,order=ascending \
        --field-config=field-path=created_at,order=descending
    """

    logger.info("[learning_agent] Starting improve() cycle")

    # Step 1 — Fetch recent resolved complaints
    try:
        complaints = (
            db.collection("complaints")
            .where("is_resolved", "==", True)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(50)
            .stream()
        )
        complaint_list = [doc.to_dict() for doc in complaints]
        logger.info(f"[learning_agent] Fetched {len(complaint_list)} resolved complaints")
    except Exception as e:
        error_msg = str(e)
        if "index" in error_msg.lower() or "failed_precondition" in error_msg.lower():
            logger.error(f"[learning_agent] Firestore index missing: {error_msg}")
            return {
                "status": "index_missing",
                "message": "Firestore composite index missing. See docstring for setup.",
                "error": error_msg
            }
        logger.error(f"[learning_agent] Firestore query failed: {e}")
        raise

    # Step 2 — Guard: need at least 5 complaints
    if len(complaint_list) < 5:
        logger.warning(f"[learning_agent] Insufficient data: {len(complaint_list)} complaints")
        return {
            "status": "insufficient_data",
            "message": "Need at least 5 resolved complaints to learn",
            "complaints_analyzed": len(complaint_list)
        }

    # Step 3 — Strip to relevant fields
    analysis_data = [
        {
            "issue_type": c.get("issue_type"),
            "urgency_level": c.get("urgency_level"),
            "customer_emotion": c.get("customer_emotion"),
            "resolution": c.get("resolution"),
            "days_since_purchase": c.get("days_since_purchase"),
            "priority": c.get("priority")
        }
        for c in complaint_list
    ]

    # Step 4 — Ask Gemini to find patterns
    logger.info(f"[learning_agent] Sending {len(analysis_data)} complaints to Gemini")
    learning_prompt = f"""
    You are an AI system optimizer analyzing customer service resolution data.

    Here are {len(analysis_data)} resolved complaints:
    {json.dumps(analysis_data, indent=2)}

    Analyze this data and return ONLY a valid JSON object, nothing else, no markdown:
    {{
        "total_analyzed": {len(analysis_data)},
        "most_common_issue": "the most frequent issue type",
        "most_common_resolution": "the most frequent resolution given",
        "pattern_insights": [
            "insight 1 about what patterns you noticed",
            "insight 2 about what works well",
            "insight 3 about areas to improve"
        ],
        "recommended_policy_updates": [
            "specific policy change recommendation 1",
            "specific policy change recommendation 2"
        ],
        "urgency_distribution": {{
            "low": "percentage",
            "medium": "percentage",
            "high": "percentage"
        }},
        "improvement_summary": "2-3 sentence summary of key learnings"
    }}
    """

    learning_response = model.generate_content(learning_prompt)

    try:
        raw = learning_response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        insights = json.loads(raw)
        logger.info("[learning_agent] Gemini insights parsed successfully")
    except json.JSONDecodeError:
        logger.warning("[learning_agent] Gemini returned invalid JSON — using fallback")
        insights = {
            "total_analyzed": len(analysis_data),
            "most_common_issue": "unknown",
            "most_common_resolution": "unknown",
            "pattern_insights": ["Insufficient data for pattern analysis"],
            "recommended_policy_updates": [],
            "improvement_summary": "Analysis incomplete due to response parsing error."
        }

    # Step 5 — Save learning report to Firestore learning_reports collection
    report_id = None
    try:
        _, doc_ref = db.collection("learning_reports").add({
            "insights": insights,
            "complaints_analyzed": len(complaint_list),
            "created_at": datetime.now(timezone.utc)
        })
        report_id = doc_ref.id
        logger.info(f"[learning_agent] Learning report saved: {report_id}")
    except Exception as e:
        logger.error(f"[learning_agent] Failed to save learning report: {e}")

    # Step 6 — MCP: save insights as a note via notes_tool.create_note()
    # Uses exact signature: create_note(title, note_type, related_entity, related_id, body, author, tags, metadata)
    try:
        note_result = create_note(
            title=f"Learning report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
            note_type="dashboard_note",
            related_entity="complaint",
            related_id=report_id or "learning_reports",
            body=insights.get("improvement_summary", "No summary available"),
            author="ResolveX Learning Agent",
            tags=[
                "auto-generated",
                "learning-agent",
                f"top-issue-{insights.get('most_common_issue', 'unknown')}",
                f"analyzed-{len(complaint_list)}-complaints"
            ],
            metadata={
                "most_common_issue": insights.get("most_common_issue"),
                "most_common_resolution": insights.get("most_common_resolution"),
                "complaints_analyzed": len(complaint_list),
                "policy_updates": insights.get("recommended_policy_updates", []),
            }
        )
        logger.info(f"[learning_agent] MCP note saved: {note_result.get('note', {}).get('note_id')}")
    except Exception as e:
        logger.error(f"[learning_agent] MCP notes_tool failed: {e}")

    logger.info(
        f"[learning_agent] Complete — {len(complaint_list)} complaints analyzed, "
        f"top issue: {insights.get('most_common_issue')}"
    )

    return {
        "status": "learned",
        "complaints_analyzed": len(complaint_list),
        "insights": insights
    }