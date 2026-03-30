import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
 
load_dotenv()
 
# Initialize Vertex AI
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
 
model = GenerativeModel("gemini-2.0-flash-001")
 
 
def listen(complaint: str) -> dict:
    """
    Receives a customer complaint, extracts key details,
    and returns an empathetic response along with structured data.
    """
 
    # Step 1 — Extract structured data from complaint
    extraction_prompt = f"""
    You are an expert customer service AI agent for a product-based company.
 
    A customer has submitted the following complaint:
    \"\"\"{complaint}\"\"\"
 
    Extract the following information and return ONLY a valid JSON object,
    nothing else, no markdown, no explanation:
    {{
        "product_name": "name of the product mentioned or 'Unknown' if not mentioned",
        "issue_type": "one of: defect / damaged / wrong_item / not_as_described / missing_parts / other",
        "order_id": "order ID if mentioned or 'Not provided'",
        "urgency_level": "one of: low / medium / high",
        "customer_emotion": "one of: frustrated / angry / disappointed / neutral / upset",
        "complaint_summary": "one sentence summary of the complaint"
    }}
    """
 
    extraction_response = model.generate_content(extraction_prompt)
 
    try:
        raw = extraction_response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        extracted_data = json.loads(raw)
    except json.JSONDecodeError:
        extracted_data = {
            "product_name": "Unknown",
            "issue_type": "other",
            "order_id": "Not provided",
            "urgency_level": "medium",
            "customer_emotion": "frustrated",
            "complaint_summary": complaint[:100]
        }
 
    # Step 2 — Generate empathetic response to customer
    response_prompt = f"""
    You are a warm, empathetic customer service agent for a product-based company.
 
    A customer has submitted this complaint:
    \"\"\"{complaint}\"\"\"
 
    The customer seems {extracted_data.get('customer_emotion', 'frustrated')}.
 
    Write a short, genuine, empathetic response that:
    - Acknowledges their frustration
    - Apologizes sincerely
    - Assures them their issue is being reviewed
    - Sounds human, not robotic
    - Is 3-4 sentences maximum
 
    Do not mention refunds or replacements yet.
    """
 
    response_result = model.generate_content(response_prompt)
    customer_message = response_result.text.strip()
 
    return {
        "status": "received",
        "customer_message": customer_message,
        "extracted_data": extracted_data
    }