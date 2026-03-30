import os
import json
from datetime import datetime, timezone
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)

model = GenerativeModel("gemini-2.0-flash-001")
db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))


def improve() -> dict:
    """
    Analyzes resolved complaints to find patterns in what
    led to the best outcomes. Updates system strategy.
    """

    # Step 1 — Fetch recent resolved complaints
    complaints = (
        db.collection("complaints")
        .where("is_resolved", "==", True)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(50)
        .stream()
    )

    complaint_list = [doc.to_dict() for doc in complaints]

    if len(complaint_list) < 5:
        return {
            "status": "insufficient_data",
            "message": "Need at least 5 resolved complaints to learn",
            "complaints_analyzed": len(complaint_list)
        }

    # Step 2 — Prepare analysis summary
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

    # Step 3 — Ask Gemini to find patterns and suggest improvements
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
    except json.JSONDecodeError:
        insights = {
            "total_analyzed": len(analysis_data),
            "most_common_issue": "unknown",
            "most_common_resolution": "unknown",
            "pattern_insights": ["Insufficient data for pattern analysis"],
            "recommended_policy_updates": [],
            "improvement_summary": "Analysis incomplete"
        }

    # Step 4 — Save learning report to Firestore
    learning_record = {
        "insights": insights,
        "complaints_analyzed": len(complaint_list),
        "created_at": datetime.now(timezone.utc)
    }

    db.collection("learning_reports").add(learning_record)

    return {
        "status": "learned",
        "complaints_analyzed": len(complaint_list),
        "insights": insights
    }