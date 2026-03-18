"""CRM tools for the MCP server.

These tool functions are called by the MCP server when Claude invokes them.
CRUD operations make ZERO LLM calls – they are pure vault I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crm_core.models.contact import Contact
from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService


def _get_svc(vault_root: Path) -> VaultService:
    return VaultService(vault_root)


# ── Contact tools ─────────────────────────────────────────────────────────────

def search_contacts(vault_root: Path, query: str) -> list[dict[str, Any]]:
    """Search contacts by free-text or field:value query.  No LLM involved."""
    qs = QuerySet(vault_root, "contact", Contact)
    if query:
        qs = qs.filter(query)
    return [c.model_dump(mode="json") for c in qs.all()]


def get_contact(vault_root: Path, slug: str) -> dict[str, Any] | None:
    """Return a single contact by slug, or None if not found."""
    svc = _get_svc(vault_root)
    try:
        return svc.read("contact", slug, Contact).model_dump(mode="json")
    except FileNotFoundError:
        return None


def create_contact(vault_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Create a new contact note from the given data dict."""
    svc = _get_svc(vault_root)
    contact = Contact(**data)
    svc.create("contact", contact)
    return contact.model_dump(mode="json")


def update_contact_status(vault_root: Path, slug: str, status: str) -> dict[str, Any]:
    """Update a contact's status field.  No LLM involved."""
    svc = _get_svc(vault_root)
    merged = svc.update("contact", slug, {"status": status})
    return merged


# ── Deal tools ────────────────────────────────────────────────────────────────

def get_deal(vault_root: Path, slug: str) -> dict[str, Any] | None:
    """Return a single deal by slug, or None if not found."""
    svc = _get_svc(vault_root)
    try:
        return svc.read("deal", slug, Deal).model_dump(mode="json")
    except FileNotFoundError:
        return None


def search_deals(vault_root: Path, query: str) -> list[dict[str, Any]]:
    """Search deals by free-text or field:value query.  No LLM involved."""
    qs = QuerySet(vault_root, "deal", Deal)
    if query:
        qs = qs.filter(query)
    return [d.model_dump(mode="json") for d in qs.all()]


def update_deal_stage(vault_root: Path, slug: str, stage: str) -> dict[str, Any]:
    """Update a deal's pipeline stage.  Triggers DAG workflow if configured."""
    svc = _get_svc(vault_root)
    merged = svc.update("deal", slug, {"stage": stage})
    return merged
