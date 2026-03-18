"""Reusable card components for CRM entities."""

from __future__ import annotations

import streamlit as st


def contact_card(contact: dict) -> None:
    """Render a compact contact card."""
    status_color = {
        "lead": "🟡",
        "prospect": "🔵",
        "customer": "🟢",
        "churned": "🔴",
    }.get(contact.get("status", ""), "⚪")

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{contact.get('name', '?')}**")
            if contact.get("email"):
                st.caption(contact["email"])
            if contact.get("company"):
                st.caption(f"🏢 {contact['company']}")
        with col2:
            st.markdown(f"{status_color} `{contact.get('status', 'unknown')}`")
            if contact.get("tags"):
                for tag in contact["tags"][:3]:
                    st.badge(tag)


def deal_card(deal: dict) -> None:
    """Render a compact deal card."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{deal.get('title', '?')}**")
            if deal.get("contact_name"):
                st.caption(f"👤 {deal['contact_name']}")
        with col2:
            value = deal.get("value", 0)
            currency = deal.get("currency", "EUR")
            prob = int(deal.get("probability", 0) * 100)
            st.metric("Value", f"{value:,.0f} {currency}")
            st.caption(f"📊 {prob}% probability")
