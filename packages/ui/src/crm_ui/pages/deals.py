"""Deals page – pipeline view and deal management."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet

st.set_page_config(page_title="Deals – RTI Obs CRM", page_icon="💼", layout="wide")

st.title("💼 Deals")

vault_str = os.environ.get("VAULT_ROOT", "")
if not vault_str:
    st.warning("Set VAULT_ROOT to your Obsidian vault path.")
    st.stop()

query = st.text_input("🔍 Search", placeholder="Acme | stage:proposal | tag:enterprise")


@st.cache_data(ttl=30)
def search_deals(vault_str: str, q: str) -> list[dict]:
    qs = QuerySet(Path(vault_str), "deal", Deal)
    if q:
        qs = qs.filter(q)
    return [d.model_dump(mode="json") for d in qs.all()]


deals = search_deals(vault_str, query)
st.caption(f"{len(deals)} deal(s) found")

if deals:
    df = pd.DataFrame(deals)
    all_cols = ["title", "stage", "value", "currency", "probability", "close_date", "contact_name", "owner"]
    display_cols = [c for c in all_cols if c in df.columns]
    if "value" in df.columns and "probability" in df.columns:
        df["forecast"] = df["value"] * df["probability"]
    display_cols_plus = display_cols + (["forecast"] if "forecast" in df.columns else [])
    st.dataframe(df[display_cols_plus], use_container_width=True, hide_index=True)

    # Totals
    total_value = df["value"].sum() if "value" in df.columns else 0
    total_forecast = df["forecast"].sum() if "forecast" in df.columns else 0
    col1, col2 = st.columns(2)
    col1.metric("Total Pipeline", f"€{total_value:,.0f}")
    col2.metric("Weighted Forecast", f"€{total_forecast:,.0f}")
else:
    st.info("No deals match your query.")

with st.expander("🔧 Raw frontmatter"):
    st.json(deals[:3])
