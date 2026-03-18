"""Main Streamlit application – CRM Dashboard.

Run with:
    streamlit run packages/ui/src/crm_ui/app.py

Or via Makefile:
    make run-ui

Design inspired by datapizza-streamlit-interface:
- Modular sidebar
- Sections with st.expander for debuggability
- st.cache_data with TTL for vault data
- Developer mode expander showing raw frontmatter
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from crm_core.models.contact import Contact
from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet

st.set_page_config(
    page_title="RTI Obs CRM",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Vault configuration ───────────────────────────────────────────────────────

def _vault_root() -> Path:
    env = os.environ.get("VAULT_ROOT")
    if env:
        return Path(env).resolve()
    # Auto-detect from project root
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "vault"
        if candidate.is_dir():
            return candidate
    st.error("VAULT_ROOT is not set. Please set it in the sidebar or as an environment variable.")
    st.stop()


@st.cache_data(ttl=60)
def load_contacts(vault_root_str: str) -> list[dict]:
    qs = QuerySet(Path(vault_root_str), "contact", Contact)
    return [c.model_dump(mode="json") for c in qs.all()]


@st.cache_data(ttl=60)
def load_deals(vault_root_str: str) -> list[dict]:
    qs = QuerySet(Path(vault_root_str), "deal", Deal)
    return [d.model_dump(mode="json") for d in qs.all()]


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🗂️ RTI Obs CRM")
    st.markdown("---")
    st.caption("Powered by Obsidian vault + DAG orchestration")
    with st.expander("⚙️ Configuration", expanded=False):
        custom_root = st.text_input("Vault Root", placeholder="/path/to/vault")
        if custom_root:
            os.environ["VAULT_ROOT"] = custom_root
    st.markdown("---")

# ── Main content ──────────────────────────────────────────────────────────────

vault_root = _vault_root()
vault_str = str(vault_root)

contacts = load_contacts(vault_str)
deals = load_deals(vault_str)

st.title("🏠 CRM Dashboard")
st.caption(f"Vault: `{vault_str}`")

# KPI row
col1, col2, col3, col4 = st.columns(4)
total_pipeline = sum(d.get("value", 0) for d in deals)
total_forecast = sum(d.get("value", 0) * d.get("probability", 0) for d in deals)
customers = sum(1 for c in contacts if c.get("status") == "customer")
leads = sum(1 for c in contacts if c.get("status") == "lead")

col1.metric("Total Contacts", len(contacts))
col2.metric("Customers", customers)
col3.metric("Pipeline Value", f"€{total_pipeline:,.0f}")
col4.metric("Forecast Value", f"€{total_forecast:,.0f}")

st.markdown("---")

# Pipeline funnel
if deals:
    import plotly.express as px

    st.subheader("📊 Pipeline Funnel")
    df_deals = pd.DataFrame(deals)
    if "stage" in df_deals.columns:
        funnel_df = df_deals.groupby("stage").agg(count=("id", "count"), value=("value", "sum")).reset_index()
        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.funnel(funnel_df, x="count", y="stage", title="Deal Count by Stage")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig2 = px.bar(funnel_df, x="stage", y="value", title="Pipeline Value by Stage", color="stage")
            st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Recent contacts
st.subheader("👤 Recent Contacts")
if contacts:
    df_c = pd.DataFrame(contacts)[["name", "email", "status", "company", "tags"]].head(10)
    st.dataframe(df_c, use_container_width=True)
else:
    st.info("No contacts found. Create your first contact in the Obsidian vault.")

# Developer expander (datapizza principle: always show raw data)
with st.expander("🔧 Developer – Raw Vault Data", expanded=False):
    tab1, tab2 = st.tabs(["Contacts JSON", "Deals JSON"])
    with tab1:
        st.json(contacts[:5])
    with tab2:
        st.json(deals[:5])
