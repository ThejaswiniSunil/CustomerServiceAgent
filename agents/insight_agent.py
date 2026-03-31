import json
import os
from typing import Any, Dict, List, Optional

import vertexai
from dotenv import load_dotenv
from google.cloud import firestore
from vertexai.generative_models import GenerativeModel

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
PATTERN_THRESHOLD = int(os.getenv("PATTERN_THRESHOLD", "3"))

vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-2.0-flash-001")
db = firestore.Client(project=PROJECT_ID)


def _clean_json_text(raw_text: str) -> str:
    return raw_text.strip().replace("```json", "").replace("```", "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _calculate_severity(total_complaints: int, issue_counts: Dict[str, int]) -> str:
    """
    Rule-based fallback severity calculator.
    """
    dominant_issue = max(issue_counts, key=issue_counts.get) if issue_counts else "unknown"

    if total_complaints >= 10:
        return "critical"
    if total_complaints >= 6:
        return "high"
    if total_complaints >= 3:
        return "medium"

    if dominant_issue in {"defect", "damaged"}:
        return "medium"

    return "low"


def _get_recent_complaints(product_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch recent complaints for a product from Firestore.
    """
    docs = (
        db.collection("complaints")
        .where("product_name", "==", product_name)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


def _build_fallback_report(
    product_name: str,
    total_complaints: int,
    issue_counts: Dict[str, int],
) -> Dict[str, Any]:
    """
    Used if Vertex AI response is unavailable or invalid.
    """
    dominant_issue = max(issue_counts, key=issue_counts.get) if issue_counts else "unknown"
    severity_level = _calculate_severity(total_complaints, issue_counts)

    return {
        "pattern_summary": (
            f"The product '{product_name}' has accumulated {total_complaints} complaints, "
            f"with '{dominant_issue}' appearing as the dominant issue pattern."
        ),
        "dominant_issue": dominant_issue,
        "severity_level": severity_level,
        "recommended_action": (
            "Conduct an immediate product quality review, inspect affected inventory, "
            "and provide a corrective action plan."
        ),
        "estimated_affected_units": str(max(total_complaints * 8, total_complaints)),
        "manufacturer_email_subject": f"Urgent Quality Escalation: {product_name}",
        "manufacturer_email_body": (
            f"Dear Manufacturer,\n\n"
            f"We are contacting you regarding a recurring quality concern involving {product_name}. "
            f"Our system has recorded {total_complaints} customer complaints, with the dominant issue "
            f"identified as '{dominant_issue}'. This suggests a potentially wider product quality problem.\n\n"
            f"We request an immediate investigation into the affected production batch, a root-cause analysis, "
            f"and a corrective action plan. Please confirm receipt of this message and provide your response "
            f"at the earliest opportunity.\n\n"
            f"Regards,\nResolveX Quality Operations"
        ),
    }


def analyze(product_name: str) -> Dict[str, Any]:
    """
    Detects recurring complaint patterns for a product and prepares
    a manufacturer escalation report if threshold is reached.
    """
    product_ref = db.collection("product_stats").document(product_name)
    product_doc = product_ref.get()

    if not product_doc.exists:
        return {
            "status": "no_data",
            "product_name": product_name,
            "pattern_detected": False,
            "total_complaints": 0,
            "issue_counts": {},
            "threshold": PATTERN_THRESHOLD,
        }

    stats = product_doc.to_dict()
    total_complaints = _safe_int(stats.get("total_complaints"), 0)
    issue_counts = stats.get("issue_counts", {}) or {}
    priority_counts = stats.get("priority_counts", {}) or {}
    resolution_counts = stats.get("resolution_counts", {}) or {}
    already_contacted = bool(stats.get("manufacturer_contacted", False))

    if total_complaints < PATTERN_THRESHOLD or already_contacted:
        return {
            "status": "monitoring",
            "product_name": product_name,
            "pattern_detected": False,
            "total_complaints": total_complaints,
            "issue_counts": issue_counts,
            "priority_counts": priority_counts,
            "resolution_counts": resolution_counts,
            "threshold": PATTERN_THRESHOLD,
            "already_contacted": already_contacted,
            "severity_level": _calculate_severity(total_complaints, issue_counts),
        }

    complaints = _get_recent_complaints(product_name, limit=20)

    complaint_summaries = [
        {
            "issue_type": complaint.get("issue_type"),
            "complaint_summary": complaint.get("complaint_summary"),
            "urgency_level": complaint.get("urgency_level"),
            "priority": complaint.get("priority"),
            "resolution": complaint.get("resolution"),
        }
        for complaint in complaints
    ]

    prompt = f"""
You are a senior product quality intelligence analyst.

You are reviewing complaint intelligence for the product "{product_name}".

Product stats:
- total complaints: {total_complaints}
- issue counts: {json.dumps(issue_counts)}
- priority counts: {json.dumps(priority_counts)}
- resolution counts: {json.dumps(resolution_counts)}

Recent complaint summaries:
{json.dumps(complaint_summaries, indent=2)}

Your task:
1. Determine whether this indicates a meaningful recurring pattern.
2. Identify the dominant issue.
3. Assess severity.
4. Recommend what the manufacturer should do.
5. Draft a professional escalation email.

Return ONLY a valid JSON object with this exact structure:
{{
  "pattern_summary": "2-3 sentence executive summary",
  "dominant_issue": "most common issue type",
  "severity_level": "one of: low / medium / high / critical",
  "recommended_action": "specific manufacturer action",
  "estimated_affected_units": "estimated number as string",
  "manufacturer_email_subject": "professional subject line",
  "manufacturer_email_body": "professional 3-4 paragraph email body"
}}

Important:
- If repeated defects or damage are present, severity should be high or critical.
- Keep the email firm, factual, and professional.
- Return JSON only.
"""

    try:
        response = model.generate_content(prompt)
        raw = _clean_json_text(response.text)
        report_data = json.loads(raw)
    except Exception:
        report_data = _build_fallback_report(product_name, total_complaints, issue_counts)

    # Normalize / validate minimal fields
    fallback = _build_fallback_report(product_name, total_complaints, issue_counts)

    final_report = {
        "pattern_summary": report_data.get("pattern_summary", fallback["pattern_summary"]),
        "dominant_issue": report_data.get("dominant_issue", fallback["dominant_issue"]),
        "severity_level": report_data.get("severity_level", fallback["severity_level"]),
        "recommended_action": report_data.get("recommended_action", fallback["recommended_action"]),
        "estimated_affected_units": report_data.get("estimated_affected_units", fallback["estimated_affected_units"]),
        "manufacturer_email_subject": report_data.get("manufacturer_email_subject", fallback["manufacturer_email_subject"]),
        "manufacturer_email_body": report_data.get("manufacturer_email_body", fallback["manufacturer_email_body"]),
    }

    product_ref.update({
        "pattern_detected": True,
        "pattern_detected_at": firestore.SERVER_TIMESTAMP,
        "pattern_report": final_report,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })

    return {
        "status": "pattern_detected",
        "product_name": product_name,
        "pattern_detected": True,
        "total_complaints": total_complaints,
        "issue_counts": issue_counts,
        "priority_counts": priority_counts,
        "resolution_counts": resolution_counts,
        "threshold": PATTERN_THRESHOLD,
        "severity_level": final_report["severity_level"],
        "pattern_summary": final_report["pattern_summary"],
        "dominant_issue": final_report["dominant_issue"],
        "recommended_action": final_report["recommended_action"],
        "estimated_affected_units": final_report["estimated_affected_units"],
        "manufacturer_email_subject": final_report["manufacturer_email_subject"],
        "manufacturer_email_body": final_report["manufacturer_email_body"],
        "report": final_report,
    }


if __name__ == "__main__":
    sample_product_name = "Voltix Charger"
    result = analyze(sample_product_name)
    print("Insight Agent Result:")
    print(result)