"""Analytics page – pipeline funnel and revenue forecast (no LLM)."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from crm_core.models.contact import Contact
from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet

st.set_page_config(page_title="Analytics – RTI Obs CRM", page_icon="📊", layout="wide")

st.title("📊 Analytics")

vault_str = os.environ.get("VAULT_ROOT", "")
if not vault_str:
    st.warning("Set VAULT_ROOT to your Obsidian vault path.")
    st.stop()

vault_root = Path(vault_str)


@st.cache_data(ttl=60)
def get_data(vault_str: str) -> tuple[list[dict], list[dict]]:
    contacts = [
        c.model_dump(mode="json")
        for c in QuerySet(Path(vault_str), "contact", Contact).all()
    ]
    deals = [
        d.model_dump(mode="json")
        for d in QuerySet(Path(vault_str), "deal", Deal).all()
    ]
    return contacts, deals


contacts, deals = get_data(vault_str)

if not deals:
    st.info("No deals in vault yet. Create some deals to see analytics.")
else:
    df = pd.DataFrame(deals)
    df["forecast"] = df["value"] * df["probability"]

    # Pipeline funnel
    st.subheader("Pipeline Funnel")
    funnel = (
        df.groupby("stage")
        .agg(count=("id", "count"), value=("value", "sum"), forecast=("forecast", "sum"))
        .reset_index()
    )
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.funnel(funnel, x="count", y="stage", title="Deal Count by Stage")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.bar(funnel, x="stage", y=["value", "forecast"], barmode="group", title="Value vs Forecast by Stage")
        st.plotly_chart(fig2, use_container_width=True)

    # Summary table
    st.subheader("Stage Summary")
    st.dataframe(
        funnel.rename(columns={"count": "Deals", "value": "Pipeline (€)", "forecast": "Forecast (€)"}),
        use_container_width=True,
    )

    # Export
    st.subheader("Export")
    col_a, col_b = st.columns(2)
    with col_a:
        if contacts:
            df_c = pd.DataFrame(contacts)
            st.download_button("⬇️ Export Contacts (CSV)", df_c.to_csv(index=False), "contacts.csv", "text/csv")
    with col_b:
        st.download_button("⬇️ Export Deals (CSV)", df.to_csv(index=False), "deals.csv", "text/csv")

if contacts:
    # Lead conversion rate
    st.subheader("Contact Status Breakdown")
    df_c = pd.DataFrame(contacts)
    status_counts = df_c["status"].value_counts().reset_index()
    fig3 = px.pie(status_counts, names="status", values="count", title="Contacts by Status")
    st.plotly_chart(fig3, use_container_width=True)
