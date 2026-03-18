"""Deals router – CRUD for vault/deals/*.md."""

from __future__ import annotations

from typing import Annotated

from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from crm_api.deps import get_vault_service

router = APIRouter()


class DealCreate(BaseModel):
    id: str
    title: str
    contact_id: str | None = None
    contact_name: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    stage: str = "lead"
    value: float = 0.0
    currency: str = "EUR"
    probability: float = 0.10
    close_date: str | None = None
    owner: str | None = None
    tags: list[str] = []


class DealUpdate(BaseModel):
    title: str | None = None
    stage: str | None = None
    value: float | None = None
    probability: float | None = None
    close_date: str | None = None
    owner: str | None = None
    tags: list[str] | None = None


@router.get("/", response_model=list[Deal])
def list_deals(
    q: Annotated[str | None, Query(description="Free-text or field:value query")] = None,
    svc: VaultService = Depends(get_vault_service),
) -> list[Deal]:
    qs = QuerySet(svc.vault_root, "deal", Deal)
    if q:
        qs = qs.filter(q)
    return qs.all()


@router.get("/{slug}", response_model=Deal)
def get_deal(slug: str, svc: VaultService = Depends(get_vault_service)) -> Deal:
    try:
        return svc.read("deal", slug, Deal)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Deal '{slug}' not found") from exc


@router.post("/", response_model=Deal, status_code=201)
def create_deal(payload: DealCreate, svc: VaultService = Depends(get_vault_service)) -> Deal:
    deal = Deal(**payload.model_dump())
    try:
        svc.create("deal", deal)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=f"Deal '{deal.id}' already exists") from exc
    return deal


@router.patch("/{slug}", response_model=Deal)
def update_deal(
    slug: str,
    payload: DealUpdate,
    svc: VaultService = Depends(get_vault_service),
) -> Deal:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")
    try:
        merged = svc.update("deal", slug, updates)
        return Deal.model_validate(merged)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Deal '{slug}' not found") from exc


@router.delete("/{slug}", status_code=204)
def delete_deal(slug: str, svc: VaultService = Depends(get_vault_service)) -> None:
    try:
        svc.delete("deal", slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Deal '{slug}' not found") from exc
