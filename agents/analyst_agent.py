from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Mock order dataset for MVP / hackathon demo
# Later this can be replaced with Firestore or an ERP / OMS integration.
MOCK_ORDERS: List[Dict[str, Any]] = [
    {
        "order_id": "ORD001",
        "customer_id": "C001",
        "product_name": "Voltix Charger",
        "purchase_date": "2026-03-27",
        "warranty_status": "valid",
        "price": 29.99,
        "currency": "USD",
        "seller": "ResolveX Store"
    },
    {
        "order_id": "ORD002",
        "customer_id": "C002",
        "product_name": "Nova Blender",
        "purchase_date": "2026-03-10",
        "warranty_status": "expired",
        "price": 89.99,
        "currency": "USD",
        "seller": "ResolveX Store"
    },
    {
        "order_id": "ORD003",
        "customer_id": "C003",
        "product_name": "AeroBuds Pro",
        "purchase_date": "2026-03-29",
        "warranty_status": "valid",
        "price": 119.99,
        "currency": "USD",
        "seller": "ResolveX Store"
    }
]


RETURN_WINDOW_DAYS = 7


def find_order(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Find an order in the mock dataset by order_id.
    """
    if not order_id or order_id == "Not provided":
        return None

    for order in MOCK_ORDERS:
        if order.get("order_id") == order_id:
            return order
    return None


def calculate_days_since_purchase(purchase_date: str) -> Optional[int]:
    """
    Returns the number of days since purchase.
    purchase_date format: YYYY-MM-DD
    """
    try:
        purchase = datetime.strptime(purchase_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - purchase).days
    except Exception:
        return None


def is_within_return_window(days_since_purchase: Optional[int], allowed_days: int = RETURN_WINDOW_DAYS) -> bool:
    """
    Returns True if purchase is within the allowed return window.
    """
    if days_since_purchase is None:
        return False
    return days_since_purchase <= allowed_days


def product_matches(extracted_data: Dict[str, Any], order: Dict[str, Any]) -> bool:
    """
    Checks whether complaint product and order product match.
    """
    complaint_product = extracted_data.get("product_name", "").strip().lower()
    order_product = order.get("product_name", "").strip().lower()
    return complaint_product == order_product


def build_response(
    *,
    order_found: bool,
    days_since_purchase: Optional[int],
    policy_applied: str,
    eligible_for: str,
    reason: str,
    order: Optional[Dict[str, Any]] = None,
    product_match: bool = False,
) -> Dict[str, Any]:
    """
    Standardized response for downstream agents.
    """
    return {
        "status": "analyzed",
        "order_found": order_found,
        "product_match": product_match,
        "days_since_purchase": days_since_purchase,
        "return_window_days": RETURN_WINDOW_DAYS,
        "within_return_window": is_within_return_window(days_since_purchase),
        "warranty_status": order.get("warranty_status", "unknown") if order else "unknown",
        "policy_applied": policy_applied,
        "eligible_for": eligible_for,
        "reason": reason,
        "order_snapshot": {
            "order_id": order.get("order_id") if order else None,
            "customer_id": order.get("customer_id") if order else None,
            "product_name": order.get("product_name") if order else None,
            "purchase_date": order.get("purchase_date") if order else None,
            "seller": order.get("seller") if order else None,
            "price": order.get("price") if order else None,
            "currency": order.get("currency") if order else None,
        } if order else None
    }


def check_eligibility(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Analyst Agent function.
    Evaluates order match, return window, warranty, and complaint type.
    Returns a structured eligibility report for the Decision Agent.
    """
    order_id = extracted_data.get("order_id", "Not provided")
    issue_type = extracted_data.get("issue_type", "other").strip().lower()
    complaint_product = extracted_data.get("product_name", "Unknown")

    order = find_order(order_id)

    # Case 1: Order not found
    if not order:
        return build_response(
            order_found=False,
            days_since_purchase=None,
            policy_applied="order_not_found_policy",
            eligible_for="escalate",
            reason=(
                f"No matching order was found for order_id '{order_id}'. "
                "This case requires manual verification."
            ),
            order=None,
            product_match=False,
        )

    # Case 2: Product mismatch
    match = product_matches(extracted_data, order)
    days_since_purchase = calculate_days_since_purchase(order.get("purchase_date", ""))

    if not match:
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="product_mismatch_policy",
            eligible_for="manual_review",
            reason=(
                f"The complaint product '{complaint_product}' does not match the order record "
                f"'{order.get('product_name')}'."
            ),
            order=order,
            product_match=False,
        )

    within_window = is_within_return_window(days_since_purchase)
    warranty_status = order.get("warranty_status", "unknown").strip().lower()

    # Case 3: Defect under warranty
    if issue_type == "defect" and warranty_status == "valid":
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="defect_under_warranty_policy",
            eligible_for="replacement",
            reason="The product is defective and the warranty is still valid.",
            order=order,
            product_match=True,
        )

    # Case 4: Damaged item within return window
    if issue_type == "damaged" and within_window:
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="damaged_item_return_window_policy",
            eligible_for="replacement",
            reason="The product was reported as damaged within the return window.",
            order=order,
            product_match=True,
        )

    # Case 5: Wrong item delivered
    if issue_type == "wrong_item":
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="wrong_item_policy",
            eligible_for="refund_or_replacement",
            reason="The customer received the wrong item.",
            order=order,
            product_match=True,
        )

    # Case 6: Missing parts within return window
    if issue_type == "missing_parts" and within_window:
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="missing_parts_policy",
            eligible_for="replacement",
            reason="The complaint indicates missing parts and the order is still within the return window.",
            order=order,
            product_match=True,
        )

    # Case 7: Not as described within return window
    if issue_type == "not_as_described" and within_window:
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="not_as_described_policy",
            eligible_for="partial_refund_or_replacement",
            reason="The product was reported as not matching its description within the return window.",
            order=order,
            product_match=True,
        )

    # Case 8: Return window expired
    if not within_window:
        return build_response(
            order_found=True,
            days_since_purchase=days_since_purchase,
            policy_applied="expired_return_window_policy",
            eligible_for="manual_review",
            reason="The return window has expired, so this case needs manual review.",
            order=order,
            product_match=True,
        )

    # Default fallback
    return build_response(
        order_found=True,
        days_since_purchase=days_since_purchase,
        policy_applied="fallback_manual_review_policy",
        eligible_for="manual_review",
        reason="The complaint did not match an automatic eligibility rule and needs review.",
        order=order,
        product_match=True,
    )


if __name__ == "__main__":
    sample_extracted_data = {
        "product_name": "Voltix Charger",
        "issue_type": "defect",
        "order_id": "ORD001",
        "urgency_level": "high",
        "customer_emotion": "frustrated",
        "complaint_summary": "My charger arrived broken and overheats after 5 minutes."
    }

    result = check_eligibility(sample_extracted_data)
    print("Analyst Agent Result:")
    print(result)