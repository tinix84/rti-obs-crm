# RTI Obs CRM 🗂️

> **Agent CRM powered by Obsidian vault + DAG orchestration**
>
> Local-first, markdown-native CRM with Claude (MCP) integration and zero-LLM CRUD.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![uv](https://img.shields.io/badge/uv-workspace-green.svg)](https://docs.astral.sh/uv/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-teal.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io)

---

## Architecture

```
Obsidian Vault (*.md + YAML frontmatter)
         │
    VaultService (python-frontmatter, atomic writes)
         │
    Pydantic v2 Models  ←→  DuckDB shadow DB
         │
    ┌────┴────────────┬───────────────┐
    │                 │               │
  FastAPI           DAG Engine     MCP Server
  REST API          (networkx)     (Claude bot)
    │                 │               │
  Streamlit UI    Workflow YAML   Claude Desktop
```

**Key design principles (from ADRs):**
- 📁 **Vault = source of truth**: all data is markdown + YAML frontmatter
- 🚫 **No LLM for CRUD**: regex/queries for search, Pydantic for validation
- 🔄 **DAG workflows**: `networkx` topological execution, zero external services
- 🔍 **Debuggable**: every LLM call logged, raw frontmatter always visible in UI

---

## Monorepo Structure

```
rti-obs-crm/
├── pyproject.toml          # uv workspace root
├── Makefile                # developer shortcuts
├── config/
│   ├── pipeline.yaml       # CRM pipeline stage definitions
│   └── workflows/          # DAG workflow YAML files
├── docs/
│   ├── usecases/           # UC1–UC5 (epics, V-model)
│   ├── requirements/       # functional + non-functional
│   └── architecture/       # system overview + ADRs
├── vault/                  # Obsidian vault (source of truth)
│   ├── .obsidian/templates/
│   ├── contacts/
│   ├── deals/
│   ├── companies/
│   └── tasks/
└── packages/
    ├── core/               # crm-core: models, vault service, DAG engine
    ├── api/                # crm-api: FastAPI REST server
    ├── bot/                # crm-bot: MCP server for Claude
    └── ui/                 # crm-ui: Streamlit dashboard
```

---

## Quick Start

```bash
# Install all workspace packages
make install

# Start the REST API
make run-api          # → http://localhost:8000/docs

# Start the Streamlit dashboard
export VAULT_ROOT=$(pwd)/vault
make run-ui           # → http://localhost:8501

# Start the MCP server (for Claude Desktop)
export VAULT_ROOT=$(pwd)/vault
make run-bot

# Build shadow DuckDB from vault
make vault-index
```

---

## Use Cases (V-model Epics)

| UC | Epic | Key Technology |
|----|------|----------------|
| UC1 | Contact Management | VaultService, Contact model, regex search |
| UC2 | Deal / Pipeline Tracking | Deal model, pipeline.yaml, DAG triggers |
| UC3 | Agent Workflow Orchestration | networkx DAG, YAML workflow definitions |
| UC4 | Bot Interface (MCP / Claude) | MCP server, PydanticAI (only for summarization) |
| UC5 | Reporting & Analytics | pandas, Plotly, Streamlit, DuckDB |

---

## Running Tests

```bash
make test            # all packages
make test-core       # crm-core only
make test-api        # crm-api only
```

---

## Adding a New Pipeline Stage

Edit `config/pipeline.yaml` — no code change required:

```yaml
stages:
  - id: demo
    label: Demo Scheduled
    order: 3
    default_probability: 0.40
```

## Adding a New Workflow

Create `config/workflows/my_workflow.yaml`:

```yaml
id: my_workflow
nodes:
  - id: step1
    type: notify
    params:
      message: "Hello {{ contact.name }}"
      channel: log
edges: []
```

Then trigger it:

```bash
curl -X POST http://localhost:8000/workflows/my_workflow/run \
  -H "Content-Type: application/json" \
  -d '{"context": {"contact": {"name": "Alice"}}}'
```

---

## References

- [Obsidian as CRM](https://www.reddit.com/r/ObsidianMD/comments/1clswlh/my_take_on_using_obsidian_as_a_crm/)
- [OpenClaw multi-agent blueprint](https://medium.com/@alirezarezvani/openclaw-multi-agent-system-the-blueprint-i-built-in-12-hours-509498d02908)
- [PydanticAI CRM tutorial](https://learnbybuilding.ai/post/learning-pydantic-ai-by-building-a-crm/)
- [Anthropic effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [datapizza-streamlit-interface](https://github.com/EnzoGitHub27/datapizza-streamlit-interface)
