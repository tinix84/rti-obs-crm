# Functional Requirements

Derived from use cases UC1–UC5 following the V-model.

## FR-01 – Contact Note CRUD
- The system **shall** create a contact `.md` file in `vault/contacts/` with YAML frontmatter conforming to the `Contact` schema.
- The system **shall** parse and validate frontmatter on read, raising `SchemaError` on mismatch.
- The system **shall** update frontmatter fields without modifying the markdown body.
- The system **shall** delete a contact note by moving it to `vault/.trash/`.

## FR-02 – Deal Note CRUD
- Same as FR-01 with the `Deal` schema and `vault/deals/` directory.
- The system **shall** validate `stage` against `config/pipeline.yaml`.

## FR-03 – Company Note CRUD
- Same as FR-01 with the `Company` schema and `vault/companies/` directory.

## FR-04 – Search (no LLM)
- The system **shall** support full-text search over frontmatter fields using regex.
- The system **shall** support structured queries: `status:customer`, `stage:Proposal`, `tag:vip`.
- Search **shall not** invoke any LLM.

## FR-05 – DAG Workflow Engine
- The system **shall** load workflow definitions from `config/workflows/*.yaml`.
- The system **shall** validate DAGs for cycles and disconnected nodes at load time.
- The system **shall** execute nodes in topological order.
- The system **shall** support node types: `action`, `condition`, `delay`, `notify`.
- Condition nodes **shall** evaluate expressions against frontmatter dicts in a sandboxed context.

## FR-06 – API REST
- The system **shall** expose `/contacts`, `/deals`, `/companies`, `/workflows` CRUD endpoints.
- The system **shall** expose `/metrics` with pipeline funnel and forecast.
- API **shall** return `application/json` and validate requests with Pydantic.

## FR-07 – MCP Bot Interface
- The system **shall** expose CRM tools via MCP stdio transport.
- CRUD tool calls **shall not** invoke LLM.
- `summarize_contact` tool **shall** use PydanticAI agent and be clearly annotated.

## FR-08 – Streamlit Dashboard
- The system **shall** render a pipeline funnel, forecast, and contact list.
- Dashboard **shall** refresh data on a configurable TTL (default 60 s).
- Export to CSV **shall** be available for contacts and deals.

## FR-09 – Vault Templates
- Each entity type (contact, deal, company, task) **shall** have an Obsidian template in `vault/.obsidian/templates/`.
- Templates **shall** include all required frontmatter fields with placeholder values.

## FR-10 – Shadow Database
- The system **shall** provide a CLI command (`make vault-index`) that reads all vault frontmatter and writes a DuckDB file `data/crm.duckdb`.
- The shadow DB **shall** have tables: `contacts`, `deals`, `companies`, `tasks`.
