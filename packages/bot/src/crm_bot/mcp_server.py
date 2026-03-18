"""MCP server for rti-obs-crm.

Exposes CRM operations as MCP tools consumable by Claude Desktop or the Claude API.

Transport: stdio (standard MCP transport)

Usage::

    python -m crm_bot.mcp_server

Or via Makefile::

    make run-bot

Configure the vault path with the VAULT_ROOT environment variable.

Tool list
---------
- search_contacts(query)   – regex/field search, no LLM
- get_contact(slug)        – read by slug, no LLM
- create_contact(data)     – write new note, no LLM
- update_contact_status    – update status field, no LLM
- search_deals(query)      – search deals, no LLM
- get_deal(slug)           – read deal, no LLM
- update_deal_stage        – update pipeline stage, no LLM
- run_workflow             – trigger DAG workflow, no LLM
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from crm_bot.tools import (
    create_contact,
    get_contact,
    get_deal,
    search_contacts,
    search_deals,
    update_contact_status,
    update_deal_stage,
)

log = logging.getLogger(__name__)


def _vault_root() -> Path:
    env = os.environ.get("VAULT_ROOT")
    if env:
        return Path(env).resolve()
    # Auto-detect: walk up from this file looking for vault/
    p = Path(__file__).resolve()
    for parent in p.parents:
        candidate = parent / "vault"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("VAULT_ROOT not set and vault/ directory not found.")


def build_server() -> Server:
    server = Server("crm-bot")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_contacts",
                description="Search CRM contacts by free-text or field:value query (e.g. 'Alice', 'status:customer').",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search query"}},
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_contact",
                description="Get a single contact by its slug (filename without .md). No LLM used.",
                inputSchema={
                    "type": "object",
                    "properties": {"slug": {"type": "string"}},
                    "required": ["slug"],
                },
            ),
            Tool(
                name="create_contact",
                description="Create a new CRM contact note. No LLM used.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "status": {"type": "string", "enum": ["lead", "prospect", "customer", "churned"]},
                        "company": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "name"],
                },
            ),
            Tool(
                name="update_contact_status",
                description="Update the status of a contact. No LLM used.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "slug": {"type": "string"},
                        "status": {"type": "string", "enum": ["lead", "prospect", "customer", "churned"]},
                    },
                    "required": ["slug", "status"],
                },
            ),
            Tool(
                name="search_deals",
                description="Search CRM deals by free-text or field:value query (e.g. 'stage:negotiation').",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_deal",
                description="Get a single deal by its slug. No LLM used.",
                inputSchema={
                    "type": "object",
                    "properties": {"slug": {"type": "string"}},
                    "required": ["slug"],
                },
            ),
            Tool(
                name="update_deal_stage",
                description="Move a deal to a new pipeline stage.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "slug": {"type": "string"},
                        "stage": {"type": "string"},
                    },
                    "required": ["slug", "stage"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        vault = _vault_root()
        try:
            match name:
                case "search_contacts":
                    result = search_contacts(vault, arguments.get("query", ""))
                case "get_contact":
                    result = get_contact(vault, arguments["slug"])
                case "create_contact":
                    result = create_contact(vault, arguments)
                case "update_contact_status":
                    result = update_contact_status(vault, arguments["slug"], arguments["status"])
                case "search_deals":
                    result = search_deals(vault, arguments.get("query", ""))
                case "get_deal":
                    result = get_deal(vault, arguments["slug"])
                case "update_deal_stage":
                    result = update_deal_stage(vault, arguments["slug"], arguments["stage"])
                case _:
                    result = {"error": f"Unknown tool: {name}"}
        except Exception as exc:
            log.exception("Tool %s failed", name)
            result = {"error": str(exc)}

        return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]

    return server


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
