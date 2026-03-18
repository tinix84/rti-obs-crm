"""Workflows page – view registered DAG workflows and trigger runs."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import yaml

st.set_page_config(page_title="Workflows – RTI Obs CRM", page_icon="⚙️", layout="wide")

st.title("⚙️ DAG Workflows")

config_dir = Path(__file__).resolve()
for parent in config_dir.parents:
    candidate = parent / "config" / "workflows"
    if candidate.is_dir():
        config_dir = candidate
        break
else:
    config_dir = None

st.markdown(
    "Workflows are defined in YAML files under `config/workflows/`. "
    "They are executed by the DAG engine with **zero LLM calls** – "
    "all routing is deterministic."
)

if config_dir and config_dir.is_dir():
    workflow_files = sorted(config_dir.glob("*.yaml"))
    for wf_file in workflow_files:
        with st.expander(f"📋 `{wf_file.stem}`", expanded=False):
            with open(wf_file) as f:
                wf_def = yaml.safe_load(f)
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Description**: {wf_def.get('description', 'N/A')}")
                st.markdown(f"**Version**: {wf_def.get('version', '?')}")
                st.markdown(f"**Nodes**: {len(wf_def.get('nodes', []))}")
                st.markdown(f"**Edges**: {len(wf_def.get('edges', []))}")
            with col2:
                st.code(yaml.dump(wf_def, default_flow_style=False), language="yaml")
else:
    st.warning("No workflow config directory found.")

st.markdown("---")

# Manual trigger (calls the REST API)
st.subheader("▶️ Trigger Workflow")

api_base = st.text_input("API Base URL", value="http://localhost:8000")
workflow_id = st.text_input("Workflow ID", placeholder="on_deal_won")
context_json = st.text_area("Context (JSON)", value='{"deal": {"title": "Test Deal", "value": 1000}}', height=100)

if st.button("🚀 Run Workflow"):
    import requests

    try:
        context = json.loads(context_json)
        r = requests.post(f"{api_base}/workflows/{workflow_id}/run", json={"context": context}, timeout=10)
        if r.ok:
            st.success(f"✅ Workflow completed: {r.json()}")
        else:
            st.error(f"❌ Error {r.status_code}: {r.text}")
    except Exception as exc:
        st.error(f"Request failed: {exc}")
