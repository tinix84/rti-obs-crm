# UC4 – Bot Interface (MCP / Claude)
**Epic**: Expose CRM operations as an MCP server so Claude Desktop / Claude API can act as a CRM assistant.

## Context
The Model Context Protocol (MCP) allows Claude to call structured tools. The bot
package exposes CRM tools over MCP (stdio transport). When LLM is genuinely needed
(e.g. summarizing a contact's interaction history) PydanticAI handles the call; for
structured CRUD operations, tools call the vault service directly (no LLM).

## Actors
- **Claude Desktop / Claude API** (MCP client)
- **MCP Server** (`crm_bot.mcp_server`)
- **Vault Service** (data layer)
- **DAG Engine** (workflow trigger)

## User Stories
| ID | Story | Priority |
|----|-------|----------|
| US-19 | As Claude I want a `search_contacts` tool to find contacts by query string | Must |
| US-20 | As Claude I want a `get_deal` tool to read deal details | Must |
| US-21 | As Claude I want a `create_contact` tool to add a new contact | Must |
| US-22 | As Claude I want a `update_deal_stage` tool to progress a deal | Must |
| US-23 | As Claude I want a `summarize_contact` tool (this one uses LLM) | Should |
| US-24 | As Claude I want a `run_workflow` tool to trigger a DAG workflow | Could |

## Acceptance Criteria
- MCP server starts on stdio and advertises all tools with JSON Schema descriptions
- Tool calls that are CRUD (US-19 to US-22, US-24) make zero LLM calls
- `summarize_contact` uses PydanticAI with explicit model annotation
- Tool responses are JSON-serialisable Pydantic models

## Out of Scope
- Slack / Teams bot (future epics)
- OAuth / multi-tenant (future)
