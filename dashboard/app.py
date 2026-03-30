"""
dashboard/app.py
─────────────────
ResolveX Dashboard — built with Streamlit.

Run with:
    streamlit run dashboard/app.py

Displays:
  - Live KPIs (total complaints, resolution breakdown, top products)
  - Complaint table with filtering
  - Product stats with pattern alerts
  - Manual complaint submission form for testing
"""

import os
import sys
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Allow importing from project root when running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Config ────────────────────────────────────────────────────────────────────

API_BASE = os.getenv("RESOLVEX_API_URL", "http://localhost:8080")

st.set_page_config(
    page_title="ResolveX Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_dashboard() -> dict:
    """Fetches the /dashboard endpoint from the ResolveX API."""
    try:
        r = requests.get(f"{API_BASE}/dashboard", timeout=10)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        st.error(f"Could not reach API at {API_BASE}: {e}")
        return {}


@st.cache_data(ttl=30)
def fetch_complaints() -> list:
    """Fetches the /complaints endpoint."""
    try:
        r = requests.get(f"{API_BASE}/complaints", timeout=10)
        r.raise_for_status()
        return r.json().get("complaints", [])
    except Exception:
        return []


@st.cache_data(ttl=30)
def fetch_products() -> list:
    """Fetches the /products endpoint."""
    try:
        r = requests.get(f"{API_BASE}/products", timeout=10)
        r.raise_for_status()
        return r.json().get("products", [])
    except Exception:
        return []


def submit_complaint(complaint_text: str) -> dict:
    """POSTs a complaint to the /complaint endpoint."""
    try:
        r = requests.post(
            f"{API_BASE}/complaint",
            json={"complaint": complaint_text},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def mark_resolved(product_name: str) -> dict:
    """POSTs to /manufacturer/resolve."""
    try:
        r = requests.post(
            f"{API_BASE}/manufacturer/resolve",
            json={"product_name": product_name},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("ResolveX")
    st.caption("Autonomous Customer Care")
    st.divider()
    st.write(f"**API:** `{API_BASE}`")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    page = st.radio(
        "Navigate",
        ["📊 Overview", "📋 Complaints", "📦 Products", "➕ Submit Complaint"],
        label_visibility="collapsed",
    )

# ── Load data ─────────────────────────────────────────────────────────────────

dashboard = fetch_dashboard()
complaints = fetch_complaints()
products = fetch_products()

# ── Page: Overview ────────────────────────────────────────────────────────────

if page == "📊 Overview":
    st.title("📊 ResolveX Overview")
    st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

    total = dashboard.get("total_complaints", len(complaints))
    resolution_breakdown = dashboard.get("resolution_breakdown", {})

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", total)
    col2.metric("Refunds", resolution_breakdown.get("refund", 0))
    col3.metric("Replacements", resolution_breakdown.get("replacement", 0))
    col4.metric("Escalated", resolution_breakdown.get("escalate", 0))

    st.divider()

    # Resolution breakdown chart
    if resolution_breakdown:
        st.subheader("Resolution Breakdown")
        df_res = pd.DataFrame(
            list(resolution_breakdown.items()),
            columns=["Resolution", "Count"]
        ).sort_values("Count", ascending=False)
        st.bar_chart(df_res.set_index("Resolution"))

    # Top products by complaints
    if products:
        st.subheader("Top Products by Complaints")
        df_prod = pd.DataFrame(products)[
            ["product_name", "total_complaints", "manufacturer_contacted", "manufacturer_resolved"]
        ].rename(columns={
            "product_name": "Product",
            "total_complaints": "Complaints",
            "manufacturer_contacted": "Mfr Contacted",
            "manufacturer_resolved": "Mfr Resolved",
        })
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

    # Recent complaints
    recent = dashboard.get("recent_complaints", complaints[:10])
    if recent:
        st.subheader("Recent Complaints")
        df_recent = pd.DataFrame(recent)[[
            "complaint_id", "product_name", "issue_type",
            "urgency_level", "resolution", "created_at"
        ]].rename(columns={
            "complaint_id": "ID",
            "product_name": "Product",
            "issue_type": "Issue",
            "urgency_level": "Urgency",
            "resolution": "Resolution",
            "created_at": "Time",
        })
        st.dataframe(df_recent, use_container_width=True, hide_index=True)

# ── Page: Complaints ──────────────────────────────────────────────────────────

elif page == "📋 Complaints":
    st.title("📋 All Complaints")

    if not complaints:
        st.info("No complaints logged yet.")
    else:
        df = pd.DataFrame(complaints)

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            product_filter = st.selectbox(
                "Filter by Product",
                ["All"] + sorted(df["product_name"].dropna().unique().tolist()),
            )
        with col2:
            resolution_filter = st.selectbox(
                "Filter by Resolution",
                ["All"] + sorted(df["resolution"].dropna().unique().tolist()),
            )
        with col3:
            urgency_filter = st.selectbox(
                "Filter by Urgency",
                ["All", "high", "medium", "low"],
            )

        if product_filter != "All":
            df = df[df["product_name"] == product_filter]
        if resolution_filter != "All":
            df = df[df["resolution"] == resolution_filter]
        if urgency_filter != "All":
            df = df[df["urgency_level"] == urgency_filter]

        display_cols = [
            "complaint_id", "product_name", "issue_type",
            "urgency_level", "customer_emotion", "resolution",
            "priority", "estimated_resolution_days", "created_at"
        ]
        existing_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[existing_cols].sort_values("created_at", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {len(df)} complaints")

# ── Page: Products ────────────────────────────────────────────────────────────

elif page == "📦 Products":
    st.title("📦 Product Intelligence")

    if not products:
        st.info("No product data yet.")
    else:
        for prod in products:
            product_name = prod.get("product_name", "Unknown")
            total = prod.get("total_complaints", 0)
            mfr_contacted = prod.get("manufacturer_contacted", False)
            mfr_resolved = prod.get("manufacturer_resolved", False)

            status_icon = "✅" if mfr_resolved else ("📨" if mfr_contacted else "🔴")
            with st.expander(f"{status_icon} **{product_name}** — {total} complaints"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Complaints", total)
                col2.metric("Mfr Contacted", "Yes" if mfr_contacted else "No")
                col3.metric("Mfr Resolved", "Yes" if mfr_resolved else "No")

                issue_counts = prod.get("issue_counts", {})
                if issue_counts:
                    df_issues = pd.DataFrame(
                        list(issue_counts.items()), columns=["Issue Type", "Count"]
                    )
                    st.bar_chart(df_issues.set_index("Issue Type"))

                if mfr_contacted and not mfr_resolved:
                    if st.button(
                        f"✅ Mark '{product_name}' as Resolved",
                        key=f"resolve_{product_name}"
                    ):
                        result = mark_resolved(product_name)
                        if result.get("success"):
                            st.success(
                                f"Marked resolved. "
                                f"{result['result'].get('customers_notified', 0)} customer(s) notified."
                            )
                            st.cache_data.clear()
                        else:
                            st.error(f"Error: {result.get('error')}")

# ── Page: Submit Complaint ────────────────────────────────────────────────────

elif page == "➕ Submit Complaint":
    st.title("➕ Submit a Complaint")
    st.caption("Use this form to test the ResolveX pipeline end-to-end.")

    sample_complaints = [
        "My Sony WH-1000XM5 headphones stopped working after 2 weeks. Order #12345.",
        "I received the wrong item — I ordered a red jumper but got a blue one. Order #98765.",
        "The Samsung TV I bought last month has a flickering screen issue. Very frustrated!",
        "My Nike trainers fell apart after only 3 uses. This is unacceptable!",
    ]

    selected_sample = st.selectbox(
        "Use a sample complaint (optional):",
        ["Custom..."] + sample_complaints
    )

    if selected_sample == "Custom...":
        complaint_text = st.text_area(
            "Your complaint:",
            height=120,
            placeholder="Describe the issue in detail..."
        )
    else:
        complaint_text = st.text_area(
            "Your complaint:",
            value=selected_sample,
            height=120,
        )

    if st.button("🚀 Submit", type="primary", use_container_width=True):
        if not complaint_text or len(complaint_text.strip()) < 10:
            st.warning("Please enter at least 10 characters.")
        else:
            with st.spinner("ResolveX is processing your complaint through all agents..."):
                result = submit_complaint(complaint_text)

            if result.get("success"):
                st.success("✅ Complaint processed successfully!")
                customer_response = result.get("customer_response", {})

                st.subheader("Customer Response")
                col1, col2 = st.columns(2)
                col1.metric("Complaint ID", result.get("complaint_id", "—"))
                col2.metric("Decision", customer_response.get("decision", "—"))
                col1.metric(
                    "Est. Resolution",
                    f"{customer_response.get('estimated_resolution_days', '?')} days"
                )

                with st.expander("Acknowledgement"):
                    st.write(customer_response.get("acknowledgement", "—"))
                with st.expander("Resolution Message"):
                    st.write(customer_response.get("resolution", "—"))
                with st.expander("Pipeline Steps Completed"):
                    for step in result.get("steps_completed", []):
                        st.write(f"  ✔ {step}")

                st.cache_data.clear()
            else:
                st.error(f"Failed: {result.get('error', result.get('detail', 'Unknown error'))}")