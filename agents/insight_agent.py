import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)

model = GenerativeModel("gemini-2.0-flash-001")
db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

# Threshold — how many complaints before alerting manufacturer
PATTERN_THRESHOLD = int(os.getenv("PATTERN_THRESHOLD", "3"))


def analyze(product_name: str) -> dict:
    """
    Analyzes complaint patterns for a product.
    Triggers manufacturer alert if threshold is reached.
    """

    # Step 1 — Get product stats from Firestore
    product_ref = db.collection("product_stats").document(product_name)
    product_doc = product_ref.get()

    if not product_doc.exists:
        return {
            "status": "no_data",
            "product_name": product_name,
            "pattern_detected": False,
            "total_complaints": 0
        }

    stats = product_doc.to_dict()
    total_complaints = stats.get("total_complaints", 0)
    issue_counts = stats.get("issue_counts", {})
    already_contacted = stats.get("manufacturer_contacted", False)

    # Step 2 — Check if pattern threshold reached
    if total_complaints < PATTERN_THRESHOLD or already_contacted:
        return {
            "status": "monitoring",
            "product_name": product_name,
            "pattern_detected": False,
            "total_complaints": total_complaints,
            "issue_counts": issue_counts,
            "threshold": PATTERN_THRESHOLD,
            "already_contacted": already_contacted
        }

    # Step 3 — Pattern detected, get recent complaints for analysis
    complaints_query = (
        db.collection("complaints")
        .where("product_name", "==", product_name)
        .limit(20)
        .stream()
    )
    complaints = [doc.to_dict() for doc in complaints_query]

    complaints_summary = [
        {
            "issue_type": c.get("issue_type"),
            "complaint_summary": c.get("complaint_summary"),
            "urgency_level": c.get("urgency_level"),
            "resolution": c.get("resolution")
        }
        for c in complaints
    ]

    # Step 4 — Generate pattern report with Gemini
    report_prompt = f"""
    You are a product quality analyst AI agent.

    You have detected a pattern: the product "{product_name}" has received
    {total_complaints} customer complaints.

    Issue breakdown: {json.dumps(issue_counts)}

    Recent complaints summary:
    {json.dumps(complaints_summary, indent=2)}

    Generate a professional manufacturer report and return ONLY a valid JSON object,
    nothing else, no markdown:
    {{
        "pattern_summary": "2-3 sentence summary of the pattern detected",
        "dominant_issue": "the most common issue type",
        "severity_level": "one of: low / medium / high / critical",
        "recommended_action": "what the manufacturer should do",
        "estimated_affected_units": "estimated number of units affected",
        "manufacturer_email_subject": "professional email subject line",
        "manufacturer_email_body": "professional 3-4 paragraph email to manufacturer demanding resolution"
    }}
    """

    report_response = model.generate_content(report_prompt)

    try:
        raw = report_response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        report_data = json.loads(raw)
    except json.JSONDecodeError:
        report_data = {
            "pattern_summary": f"{product_name} has {total_complaints} complaints",
            "dominant_issue": max(issue_counts, key=issue_counts.get) if issue_counts else "unknown",
            "severity_level": "high",
            "recommended_action": "Immediate quality review required",
            "estimated_affected_units": str(total_complaints * 10),
            "manufacturer_email_subject": f"Quality Issue Report: {product_name}",
            "manufacturer_email_body": f"We have received {total_complaints} complaints about {product_name}."
        }

    # Step 5 — Mark product as pattern detected in Firestore
    product_ref.update({
        "pattern_detected": True,
        "pattern_report": report_data,
        "pattern_detected_at": firestore.SERVER_TIMESTAMP
    })

    return {
        "status": "pattern_detected",
        "product_name": product_name,
        "pattern_detected": True,
        "total_complaints": total_complaints,
        "issue_counts": issue_counts,
        "severity_level": report_data.get("severity_level"),
        "pattern_summary": report_data.get("pattern_summary"),
        "dominant_issue": report_data.get("dominant_issue"),
        "recommended_action": report_data.get("recommended_action"),
        "manufacturer_email_subject": report_data.get("manufacturer_email_subject"),
        "manufacturer_email_body": report_data.get("manufacturer_email_body"),
        "report": report_data
    }