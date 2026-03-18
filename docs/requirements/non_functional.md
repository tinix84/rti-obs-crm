# Non-Functional Requirements

## NFR-01 – Performance
- Vault search over 1 000 notes **shall** complete in < 500 ms (regex, no LLM).
- API response time for CRUD operations **shall** be < 100 ms (p95, local filesystem).
- Dashboard data load **shall** be < 2 s for vault ≤ 1 000 notes.

## NFR-02 – Reliability
- The vault service **shall** never corrupt an existing markdown body during frontmatter update (atomic write with temp file + rename).
- The DAG engine **shall** log execution errors to vault and not raise unhandled exceptions to callers.

## NFR-03 – Maintainability
- All packages follow the `src/` layout and are installable as standalone pip packages.
- Code coverage **shall** be ≥ 80 % for `packages/core`.
- All public functions have type annotations.

## NFR-04 – Extensibility
- New pipeline stages **shall** be addable via `config/pipeline.yaml` without code change.
- New workflow node types **shall** be registrable via a plugin entry-point pattern.
- New API routers **shall** be addable by dropping a file in `packages/api/src/crm_api/routers/`.

## NFR-05 – Security
- No secrets (API keys, passwords) **shall** be committed to the repository.
- Secrets **shall** be loaded from environment variables or `.env` files (gitignored).
- MCP server **shall** run with least-privilege (read-only vault access by default).
- Condition node `eval` **shall** be sandboxed (no `__builtins__` access).

## NFR-06 – Portability
- The system **shall** run on Linux, macOS, and Windows (WSL2).
- Python ≥ 3.12 required.
- No mandatory external services at startup (all-local mode must work offline).

## NFR-07 – Debuggability (datapizza principle)
- Every LLM call **shall** log prompt, model, latency, and response to `logs/llm_calls.jsonl`.
- Every DAG execution step **shall** emit a structured log line (JSON).
- Streamlit pages **shall** include a developer expander showing raw frontmatter.
