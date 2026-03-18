# System Architecture Overview

## Vision
`rti-obs-crm` is a **local-first, agent-ready CRM** where all business data lives as
Markdown files in an Obsidian vault. YAML frontmatter acts as a "shadow database"
that can be synced to DuckDB for analytics. A DAG engine orchestrates business
workflows. Claude (via MCP) acts as a conversational interface for power users.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │  Obsidian UI │  │ Streamlit UI │  │ Claude Desktop (MCP)   ││
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────┘│
└─────────┼─────────────────┼────────────────────── ┼─────────────┘
          │ direct vault     │ HTTP REST             │ MCP stdio
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  packages/api  (FastAPI)          packages/bot  (MCP Server)    │
│  /contacts  /deals  /metrics      tools: search, create, update │
└────────────────────────┬────────────────────────────────────────┘
                         │ Python import
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  packages/core                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  vault/service  │  │  vault/query    │  │  dag/engine    │  │
│  │  (frontmatter   │  │  (regex search, │  │  (networkx     │  │
│  │   CRUD)         │  │   no LLM)       │  │   topo sort)   │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
│           │                    │                    │           │
│  ┌────────▼────────────────────▼────────────────────▼────────┐  │
│  │  models/ (Pydantic v2)                                     │  │
│  │  Contact | Deal | Company | Task | WorkflowRun             │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ read/write .md files
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  vault/  (Obsidian Vault – source of truth)                      │
│  contacts/  deals/  companies/  tasks/  workflows/runs/          │
│  Each file: YAML frontmatter + Markdown body                     │
└────────────────────────────────────┬────────────────────────────┘
                                     │ make vault-index
                                     ▼
                           data/crm.duckdb  (shadow DB)
```

## Package Responsibilities

| Package | Language | Responsibility |
|---------|----------|----------------|
| `crm-core` | Python | Pydantic models, vault CRUD, DAG engine, query |
| `crm-api` | Python | FastAPI REST server, depends on crm-core |
| `crm-bot` | Python | MCP server + PydanticAI agent, depends on crm-core |
| `crm-ui` | Python | Streamlit dashboard, depends on crm-core |

## Data Flow – Creating a Contact

```
User fills template in Obsidian
        │
        ▼
vault/contacts/<slug>.md  ←── YAML frontmatter (Contact schema)
        │                       + Markdown body (free notes)
        ▼
VaultService.read(path)   ──► Contact (Pydantic model, validated)
        │
        ▼  (optional)
make vault-index  ──► INSERT INTO contacts ... in data/crm.duckdb
```

## Data Flow – Deal Won Workflow

```
PUT /deals/{id}/stage  {stage: "Won"}
        │
        ▼
VaultService.update_frontmatter(deal_path, {stage: "Won"})
        │
        ▼
DAGEngine.trigger("on_deal_won", context={deal: {...}})
        │
        ▼
Execute nodes in topological order:
  1. notify_owner  (action node – log message)
  2. create_invoice_task  (action node – creates task note)
  3. update_contact_status  (action node – sets contact status=customer)
        │
        ▼
vault/workflows/runs/on_deal_won/<run_id>.md  (execution log)
```

## Key Design Decisions

See `docs/architecture/ADR/` for full records.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data storage | Obsidian vault (`.md` + frontmatter) | Local-first, human-readable, no server required |
| Shadow DB | DuckDB | Fast analytical queries on frontmatter, serverless |
| DAG library | `networkx` | Zero-dependency graph algorithms, topological sort |
| Agent framework | `pydantic-ai` | Type-safe, debuggable, supports multiple LLM backends |
| API framework | FastAPI + Pydantic v2 | Auto-generated OpenAPI, async, standard choice |
| UI framework | Streamlit | Rapid dashboard, datapizza-inspired, no JS required |
| Bot protocol | MCP (stdio) | Native Claude Desktop support, JSON-schema tools |
| LLM usage | Minimal | Regex/queries for CRUD; LLM only for summarization (UC4) |

## Directory Layout

```
rti-obs-crm/
├── pyproject.toml          # uv workspace root
├── Makefile                # developer shortcuts
├── .python-version         # 3.12
├── config/
│   ├── pipeline.yaml       # CRM pipeline stage definitions
│   └── workflows/          # DAG workflow YAML files
├── docs/
│   ├── usecases/           # UC1-UC5 (epics)
│   ├── requirements/       # functional + non-functional
│   └── architecture/       # this file + ADRs
├── vault/                  # Obsidian vault (source of truth)
│   ├── .obsidian/templates/
│   ├── contacts/
│   ├── deals/
│   ├── companies/
│   ├── tasks/
│   └── workflows/runs/
├── packages/
│   ├── core/               # crm-core package
│   ├── api/                # crm-api package
│   ├── bot/                # crm-bot package
│   └── ui/                 # crm-ui package
└── data/                   # gitignored – DuckDB shadow DB
```
