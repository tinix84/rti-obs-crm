"""Contacts router – CRUD for vault/contacts/*.md."""

from __future__ import annotations

from typing import Annotated

from crm_core.models.contact import Contact, ContactStatus
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from crm_api.deps import get_vault_service

router = APIRouter()


class ContactCreate(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    company_id: str | None = None
    status: ContactStatus = ContactStatus.LEAD
    tags: list[str] = []
    source: str | None = None
    owner: str | None = None
    linkedin: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    status: ContactStatus | None = None
    tags: list[str] | None = None
    source: str | None = None
    owner: str | None = None


@router.get("/", response_model=list[Contact])
def list_contacts(
    q: Annotated[str | None, Query(description="Free-text or field:value query")] = None,
    svc: VaultService = Depends(get_vault_service),
) -> list[Contact]:
    """List all contacts, optionally filtered by *q* (no LLM)."""
    qs = QuerySet(svc.vault_root, "contact", Contact)
    if q:
        qs = qs.filter(q)
    return qs.all()


@router.get("/{slug}", response_model=Contact)
def get_contact(slug: str, svc: VaultService = Depends(get_vault_service)) -> Contact:
    try:
        return svc.read("contact", slug, Contact)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Contact '{slug}' not found") from exc


@router.post("/", response_model=Contact, status_code=201)
def create_contact(
    payload: ContactCreate,
    svc: VaultService = Depends(get_vault_service),
) -> Contact:
    contact = Contact(**payload.model_dump())
    try:
        svc.create("contact", contact)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=f"Contact with id '{contact.id}' already exists") from exc
    return contact


@router.patch("/{slug}", response_model=Contact)
def update_contact(
    slug: str,
    payload: ContactUpdate,
    svc: VaultService = Depends(get_vault_service),
) -> Contact:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")
    try:
        merged = svc.update("contact", slug, updates)
        return Contact.model_validate(merged)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Contact '{slug}' not found") from exc


@router.delete("/{slug}", status_code=204)
def delete_contact(slug: str, svc: VaultService = Depends(get_vault_service)) -> None:
    try:
        svc.delete("contact", slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Contact '{slug}' not found") from exc
