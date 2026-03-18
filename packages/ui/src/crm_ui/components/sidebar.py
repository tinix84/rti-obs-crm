"""Shared sidebar component (datapizza-inspired modular sidebar)."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    """Render the application sidebar with navigation and vault info."""
    with st.sidebar:
        st.title("🗂️ RTI Obs CRM")
        st.markdown("---")

        st.subheader("📌 Navigation")
        st.page_link("app.py", label="🏠 Dashboard", icon="🏠")
        st.page_link("pages/contacts.py", label="👤 Contacts")
        st.page_link("pages/deals.py", label="💼 Deals")
        st.page_link("pages/workflows.py", label="⚙️ Workflows")
        st.page_link("pages/analytics.py", label="📊 Analytics")

        st.markdown("---")

        with st.expander("⚙️ Configuration", expanded=False):
            st.text_input("Vault Root", key="vault_root_input", placeholder="/path/to/vault")
            st.caption("Set VAULT_ROOT env var to persist this setting.")
