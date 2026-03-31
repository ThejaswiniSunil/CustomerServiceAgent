from datetime import datetime
from typing import Dict, Any, List


MOCK_ORDERS: List[Dict[str, Any]] = [
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


def find_order(order_id: str) -> Dict[str, Any] | None:
    for order in MOCK_ORDERS:
        if order.get("order_id") == order_id:
            return order
    return None


def check_return_window(purchase_date: str, allowed_days: int = 7) -> Dict[str, Any]:
    try:
        purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
        today = datetime.today()
        days_since_purchase = (today - purchase).days

        return {
            "within_window": days_since_purchase <= allowed_days,
            "days_since_purchase": days_since_purchase
        }
    except Exception:
        return {
            "within_window": False,
            "days_since_purchase": None
        }


def check_product_match(listener_output: Dict[str, Any], order: Dict[str, Any]) -> bool:
    complaint_product = listener_output.get("product_name", "").strip().lower()
    ordered_product = order.get("product_name", "").strip().lower()
    return complaint_product == ordered_product


def check_eligibility(listener_output: Dict[str, Any]) -> Dict[str, Any]:
    order_id = listener_output.get("order_id", "Not provided")
    issue_type = listener_output.get("issue_type", "other").strip().lower()

    order = find_order(order_id)

    if not order:
        return {
            "order_found": False,
            "days_since_purchase": None,
            "policy_applied": "order_not_found",
            "eligible_for": "escalate",
            "reason": "Order not found in the system."
        }

    product_match = check_product_match(listener_output, order)
    return_window = check_return_window(order.get("purchase_date", ""))
    warranty_status = order.get("warranty_status", "invalid").lower()

    if not product_match:
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "product_mismatch",
            "eligible_for": "manual_review",
            "reason": "The product in the complaint does not match the product in the order."
        }

    if issue_type == "defect" and warranty_status == "valid":
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "defect_under_warranty",
            "eligible_for": "replacement",
            "reason": "Defective product under valid warranty."
        }

    if issue_type == "wrong_item":
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "wrong_item_policy",
            "eligible_for": "refund_or_replacement",
            "reason": "Wrong item was delivered."
        }

    if issue_type == "damaged" and return_window["within_window"]:
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "damaged_within_return_window",
            "eligible_for": "replacement",
            "reason": "Damaged item reported within return window."
        }

    if issue_type == "missing_parts" and return_window["within_window"]:
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "missing_parts_policy",
            "eligible_for": "replacement",
            "reason": "Missing parts reported within return window."
        }

    if not return_window["within_window"]:
        return {
            "order_found": True,
            "days_since_purchase": return_window["days_since_purchase"],
            "policy_applied": "return_window_expired",
            "eligible_for": "manual_review",
            "reason": "Return window has expired."
        }

    return {
        "order_found": True,
        "days_since_purchase": return_window["days_since_purchase"],
        "policy_applied": "manual_review_fallback",
        "eligible_for": "manual_review",
        "reason": "This complaint needs manual review."
    }