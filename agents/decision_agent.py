import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
 
load_dotenv()
 
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
 
model = GenerativeModel("gemini-2.0-flash-001")
 
 
def decide(extracted_data: dict, eligibility: dict) -> dict:
    """
    Takes analyst eligibility report and makes final
    refund or replacement decision. Notifies customer.
    """
 
    product_name = extracted_data.get("product_name", "Unknown")
    issue_type = extracted_data.get("issue_type", "other")
    urgency_level = extracted_data.get("urgency_level", "medium")
    customer_emotion = extracted_data.get("customer_emotion", "frustrated")
    complaint_summary = extracted_data.get("complaint_summary", "")
    eligible_for = eligibility.get("eligible_for", "none")
    reason = eligibility.get("reason", "")
 
    # Step 1 — Make decision using Gemini
    decision_prompt = f"""
    You are a senior customer service decision agent.
 
    Customer complaint summary: {complaint_summary}
    Product: {product_name}
    Issue type: {issue_type}
    Urgency: {urgency_level}
    Customer emotion: {customer_emotion}
    Eligibility result: {eligible_for}
    Eligibility reason: {reason}
 
    Based on this, decide the resolution and return ONLY a valid JSON object,
    nothing else, no markdown, no explanation:
    {{
        "decision": "one of: full_refund / replacement / partial_refund / escalate",
        "decision_reason": "one sentence explaining why this decision was made",
        "priority": "one of: low / medium / high / urgent",
        "next_action": "one sentence describing what happens next",
        "estimated_resolution_days": "number of days to resolve as integer"
    }}
    """
 
    decision_response = model.generate_content(decision_prompt)
 
    try:
        raw = decision_response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        decision_data = json.loads(raw)
    except json.JSONDecodeError:
        decision_data = {
            "decision": "escalate",
            "decision_reason": "Could not process automatically",
            "priority": "high",
            "next_action": "Manual review required",
            "estimated_resolution_days": 3
        }
 
    # Step 2 — Generate customer notification message
    message_prompt = f"""
    You are a warm, empathetic customer service agent.
 
    You have made the following decision for a customer:
    Decision: {decision_data.get('decision')}
    Product: {product_name}
    Reason: {decision_data.get('decision_reason')}
    Next action: {decision_data.get('next_action')}
    Customer emotion: {customer_emotion}
    Estimated resolution: {decision_data.get('estimated_resolution_days')} days
 
    Write a clear, warm, professional message to the customer that:
    - Tells them exactly what was decided
    - Explains what happens next and timeline
    - Makes them feel valued and heard
    - Is 3-5 sentences maximum
    - Sounds human, not robotic
    """
 
    message_response = model.generate_content(message_prompt)
    customer_message = message_response.text.strip()
 
    return {
        "status": "decided",
        "decision": decision_data.get("decision"),
        "decision_reason": decision_data.get("decision_reason"),
        "priority": decision_data.get("priority"),
        "next_action": decision_data.get("next_action"),
        "estimated_resolution_days": decision_data.get("estimated_resolution_days"),
        "customer_message": customer_message,
        "product_name": product_name,
        "issue_type": issue_type
    }