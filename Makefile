.PHONY: install lint test run-api run-ui run-bot sync

## ── Bootstrap ─────────────────────────────────────────────────────────────
install:          ## Install all workspace packages
	uv sync --all-packages

## ── Code quality ──────────────────────────────────────────────────────────
lint:             ## Ruff lint + format check
	uv run ruff check .
	uv run ruff format --check .

format:           ## Auto-format with ruff
	uv run ruff format .
	uv run ruff check --fix .

type-check:       ## Mypy type checks
	uv run mypy packages/core/src packages/api/src packages/bot/src packages/ui/src

## ── Tests ──────────────────────────────────────────────────────────────────
test:             ## Run all tests
	uv run pytest --cov=packages --cov-report=term-missing -q

test-core:        ## Run core package tests only
	uv run pytest packages/core/tests -v

test-api:         ## Run API package tests only
	uv run pytest packages/api/tests -v

## ── Run services ───────────────────────────────────────────────────────────
run-api:          ## Start FastAPI server (uvicorn)
	uv run uvicorn crm_api.main:app --reload --port 8000

run-ui:           ## Start Streamlit UI
	uv run streamlit run packages/ui/src/crm_ui/app.py --server.port 8501

run-bot:          ## Start MCP server (stdio transport)
	uv run python -m crm_bot.mcp_server

## ── Vault ──────────────────────────────────────────────────────────────────
vault-index:      ## Rebuild the shadow database from vault frontmatter
	uv run python -m crm_core.vault.index vault/

vault-validate:   ## Validate all vault frontmatter schemas
	uv run python -m crm_core.vault.validate vault/

help:             ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
