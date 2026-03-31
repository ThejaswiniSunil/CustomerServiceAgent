import json
import os
from typing import Any, Dict

import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel

load_dotenv()

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

model = GenerativeModel("gemini-2.0-flash-001")


ALLOWED_DECISIONS = {
    "full_refund",
    "replacement",
    "partial_refund",
    "escalate",
}

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}


def _clean_json_text(raw_text: str) -> str:
    """
    Removes markdown code fences if the model returns them.
    """
    return raw_text.strip().replace("```json", "").replace("```", "").strip()


def _safe_decision_fallback(extracted_data: Dict[str, Any], eligibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reliable fallback if model output fails or is invalid.
    """
    issue_type = extracted_data.get("issue_type", "other")
    urgency_level = extracted_data.get("urgency_level", "medium")
    eligible_for = eligibility.get("eligible_for", "manual_review")
    reason = eligibility.get("reason", "Automatic decision could not be completed.")

    if eligible_for == "replacement":
        decision = "replacement"
    elif eligible_for in {"refund_or_replacement", "partial_refund_or_replacement"}:
        decision = "partial_refund"
    elif eligible_for == "escalate":
        decision = "escalate"
    else:
        decision = "escalate"

    if urgency_level == "high" or issue_type in {"defect", "damaged"}:
        priority = "high"
    else:
        priority = "medium"

    return {
        "decision": decision,
        "decision_reason": reason,
        "priority": priority,
        "next_action": "The case will proceed based on policy and be tracked in the system.",
        "estimated_resolution_days": 3,
    }


def _validate_decision(decision_data: Dict[str, Any], extracted_data: Dict[str, Any], eligibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures decision output is valid and normalized.
    """
    fallback = _safe_decision_fallback(extracted_data, eligibility)

    decision = decision_data.get("decision", fallback["decision"])
    if decision not in ALLOWED_DECISIONS:
        decision = fallback["decision"]

    priority = decision_data.get("priority", fallback["priority"])
    if priority not in ALLOWED_PRIORITIES:
        priority = fallback["priority"]

    try:
        estimated_days = int(decision_data.get("estimated_resolution_days", fallback["estimated_resolution_days"]))
        if estimated_days < 1:
            estimated_days = fallback["estimated_resolution_days"]
    except Exception:
        estimated_days = fallback["estimated_resolution_days"]

    return {
        "decision": decision,
        "decision_reason": decision_data.get("decision_reason", fallback["decision_reason"]),
        "priority": priority,
        "next_action": decision_data.get("next_action", fallback["next_action"]),
        "estimated_resolution_days": estimated_days,
    }


def decide(extracted_data: Dict[str, Any], eligibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Makes the final business decision using complaint context + analyst output.
    Also generates a warm customer-facing message.
    """
    product_name = extracted_data.get("product_name", "Unknown")
    issue_type = extracted_data.get("issue_type", "other")
    urgency_level = extracted_data.get("urgency_level", "medium")
    customer_emotion = extracted_data.get("customer_emotion", "frustrated")
    complaint_summary = extracted_data.get("complaint_summary", "")
    eligible_for = eligibility.get("eligible_for", "manual_review")
    analyst_reason = eligibility.get("reason", "")
    days_since_purchase = eligibility.get("days_since_purchase")
    within_return_window = eligibility.get("within_return_window", False)
    warranty_status = eligibility.get("warranty_status", "unknown")

    # Step 1: Ask Gemini for a structured decision
    decision_prompt = f"""
You are a senior customer care decision agent for an enterprise returns and resolution platform.

Your task is to make the final case decision based on:
- customer complaint details
- analyst eligibility findings
- business fairness
- urgency and sentiment

Complaint summary: {complaint_summary}
Product: {product_name}
Issue type: {issue_type}
Urgency level: {urgency_level}
Customer emotion: {customer_emotion}

Analyst output:
- eligible_for: {eligible_for}
- analyst_reason: {analyst_reason}
- days_since_purchase: {days_since_purchase}
- within_return_window: {within_return_window}
- warranty_status: {warranty_status}

Return ONLY a valid JSON object with this exact structure:
{{
  "decision": "one of: full_refund / replacement / partial_refund / escalate",
  "decision_reason": "one clear sentence explaining the business reason",
  "priority": "one of: low / medium / high / urgent",
  "next_action": "one short sentence describing what happens next",
  "estimated_resolution_days": 1
}}

Important rules:
- If product is defective and eligible for replacement, prefer replacement.
- If wrong item delivered, prefer full_refund or replacement depending on fairness.
- If case is unclear or unsupported, use escalate.
- If sentiment is angry and issue is serious, priority should be high or urgent.
- Return JSON only. No markdown. No extra text.
"""

    try:
        decision_response = model.generate_content(decision_prompt)
        raw = _clean_json_text(decision_response.text)
        parsed_decision = json.loads(raw)
    except Exception:
        parsed_decision = _safe_decision_fallback(extracted_data, eligibility)

    final_decision = _validate_decision(parsed_decision, extracted_data, eligibility)

    # Step 2: Generate customer-facing message
    message_prompt = f"""
You are a warm, empathetic, premium customer service representative.

A final decision has been made for a customer complaint.

Product: {product_name}
Issue summary: {complaint_summary}
Customer emotion: {customer_emotion}
Decision: {final_decision['decision']}
Decision reason: {final_decision['decision_reason']}
Next action: {final_decision['next_action']}
Estimated resolution time: {final_decision['estimated_resolution_days']} days

Write a professional message to the customer that:
- acknowledges their experience respectfully
- clearly explains the decision
- explains what happens next
- sounds human, polished, and reassuring
- is 3 to 5 sentences maximum
- avoids robotic language

Return only the message text.
"""

    try:
        message_response = model.generate_content(message_prompt)
        customer_message = message_response.text.strip()
    except Exception:
        customer_message = (
            f"We’re sorry for the inconvenience you experienced with {product_name}. "
            f"After reviewing your case, we have decided on {final_decision['decision'].replace('_', ' ')}. "
            f"{final_decision['next_action']} "
            f"We appreciate your patience while we resolve this within approximately "
            f"{final_decision['estimated_resolution_days']} day(s)."
        )

    return {
        "status": "decided",
        "decision": final_decision["decision"],
        "decision_reason": final_decision["decision_reason"],
        "priority": final_decision["priority"],
        "next_action": final_decision["next_action"],
        "estimated_resolution_days": final_decision["estimated_resolution_days"],
        "customer_message": customer_message,
        "product_name": product_name,
        "issue_type": issue_type,
    }


if __name__ == "__main__":
    sample_extracted_data = {
        "product_name": "Voltix Charger",
        "issue_type": "defect",
        "order_id": "ORD001",
        "urgency_level": "high",
        "customer_emotion": "frustrated",
        "complaint_summary": "My charger arrived broken and overheats after 5 minutes."
    }

    sample_eligibility = {
        "status": "analyzed",
        "order_found": True,
        "product_match": True,
        "days_since_purchase": 3,
        "return_window_days": 7,
        "within_return_window": True,
        "warranty_status": "valid",
        "policy_applied": "defect_under_warranty_policy",
        "eligible_for": "replacement",
        "reason": "The product is defective and the warranty is still valid.",
    }

    result = decide(sample_extracted_data, sample_eligibility)
    print("Decision Agent Result:")
    print(result)