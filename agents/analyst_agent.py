from datetime import datetime
from typing import Dict, List, Any


def find_order(order_id: str, orders: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Find an order by order_id from the mock orders list.
    """
    for order in orders:
        if order.get("order_id") == order_id:
            return order
    return None


def check_return_window(purchase_date: str, allowed_days: int = 7) -> Dict[str, Any]:
    """
    Check whether the purchase is still within the return window.
    purchase_date format: YYYY-MM-DD
    """
    try:
        purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
        today = datetime.today()
        days_since_purchase = (today - purchase).days

        return {
            "within_window": days_since_purchase <= allowed_days,
            "days_since_purchase": days_since_purchase,
            "allowed_days": allowed_days
        }
    except Exception as e:
        return {
            "within_window": False,
            "days_since_purchase": None,
            "allowed_days": allowed_days,
            "error": f"Invalid purchase date: {str(e)}"
        }


def check_product_match(listener_output: Dict[str, Any], order: Dict[str, Any]) -> bool:
    """
    Checks whether the product from the complaint matches the product in the order.
    """
    complaint_product = listener_output.get("product_name", "").strip().lower()
    ordered_product = order.get("product_name", "").strip().lower()
    return complaint_product == ordered_product


def analyze_eligibility(listener_output: Dict[str, Any], orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main analyst function.
    Takes listener output + order dataset and returns eligibility analysis.
    """

    order_id = listener_output.get("order_id")
    issue_type = listener_output.get("issue_type", "").strip().lower()

    order = find_order(order_id, orders)

    if not order:
        return {
            "order_found": False,
            "product_match": False,
            "warranty_status": "unknown",
            "return_window_status": "not_eligible",
            "policy_eligible": False,
            "recommended_action": "escalate",
            "analysis_reason": "Order not found in the system."
        }

    product_match = check_product_match(listener_output, order)
    return_window_result = check_return_window(order.get("purchase_date", ""))
    warranty_status = order.get("warranty_status", "invalid").strip().lower()

    if not product_match:
        return {
            "order_found": True,
            "product_match": False,
            "warranty_status": warranty_status,
            "return_window_status": "eligible" if return_window_result["within_window"] else "expired",
            "policy_eligible": False,
            "recommended_action": "manual_review",
            "analysis_reason": "The product in the complaint does not match the product in the order."
        }

    # Rule 1: defective item + valid warranty = replacement
    if issue_type == "defective item" and warranty_status == "valid":
        return {
            "order_found": True,
            "product_match": True,
            "warranty_status": warranty_status,
            "return_window_status": "eligible" if return_window_result["within_window"] else "expired",
            "policy_eligible": True,
            "recommended_action": "replacement",
            "analysis_reason": "Defective item reported and warranty is valid."
        }

    # Rule 2: wrong item delivered = refund or replacement
    if issue_type == "wrong item":
        return {
            "order_found": True,
            "product_match": True,
            "warranty_status": warranty_status,
            "return_window_status": "eligible" if return_window_result["within_window"] else "expired",
            "policy_eligible": True,
            "recommended_action": "refund_or_replacement",
            "analysis_reason": "Wrong item was delivered to the customer."
        }

    # Rule 3: damaged item within return window = replacement
    if issue_type == "damaged item" and return_window_result["within_window"]:
        return {
            "order_found": True,
            "product_match": True,
            "warranty_status": warranty_status,
            "return_window_status": "eligible",
            "policy_eligible": True,
            "recommended_action": "replacement",
            "analysis_reason": "Damaged item reported within the return window."
        }

    # Rule 4: return window expired
    if not return_window_result["within_window"]:
        return {
            "order_found": True,
            "product_match": True,
            "warranty_status": warranty_status,
            "return_window_status": "expired",
            "policy_eligible": False,
            "recommended_action": "manual_review",
            "analysis_reason": "Return window has expired."
        }

    # Default fallback
    return {
        "order_found": True,
        "product_match": True,
        "warranty_status": warranty_status,
        "return_window_status": "eligible" if return_window_result["within_window"] else "expired",
        "policy_eligible": False,
        "recommended_action": "manual_review",
        "analysis_reason": "This complaint needs human review based on policy."
    }


# -----------------------------
# Testing the analyst agent
# -----------------------------
if __name__ == "__main__":
    mock_orders = [
        {
            "order_id": "ORD001",
            "customer_id": "C001",
            "product_name": "Voltix Charger",
            "purchase_date": "2026-03-27",
            "warranty_status": "valid"
        },
        {
            "order_id": "ORD002",
            "customer_id": "C002",
            "product_name": "Nova Blender",
            "purchase_date": "2026-03-10",
            "warranty_status": "expired"
        }
    ]

    sample_listener_output = {
        "customer_id": "C001",
        "order_id": "ORD001",
        "product_name": "Voltix Charger",
        "issue_type": "defective item",
        "urgency": "high",
        "sentiment": "frustrated",
        "requested_action": "replacement",
        "complaint_text": "My charger arrived broken and overheats."
    }

    result = analyze_eligibility(sample_listener_output, mock_orders)
    print("Analyst Agent Result:")
    print(result)