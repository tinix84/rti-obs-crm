"""Contacts page – search, view, and manage contacts."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from crm_core.models.contact import Contact
from crm_core.vault.query import QuerySet

st.set_page_config(page_title="Contacts – RTI Obs CRM", page_icon="👤", layout="wide")

st.title("👤 Contacts")

vault_str = os.environ.get("VAULT_ROOT", "")
if not vault_str:
    st.warning("Set VAULT_ROOT to your Obsidian vault path.")
    st.stop()

vault_root = Path(vault_str)

# Search bar
query = st.text_input("🔍 Search", placeholder="Alice | status:customer | tag:vip")

@st.cache_data(ttl=30)
def search(vault_str: str, q: str) -> list[dict]:
    qs = QuerySet(Path(vault_str), "contact", Contact)
    if q:
        qs = qs.filter(q)
    return [c.model_dump(mode="json") for c in qs.all()]


contacts = search(vault_str, query)

st.caption(f"{len(contacts)} contact(s) found")

if contacts:
    import pandas as pd

    df = pd.DataFrame(contacts)
    display_cols = [c for c in ["name", "email", "status", "company", "tags", "owner"] if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No contacts match your query.")

# Developer expander
with st.expander("🔧 Raw frontmatter"):
    st.json(contacts[:3])
