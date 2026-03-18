"""Companies router – CRUD for vault/companies/*.md."""

from __future__ import annotations

from typing import Annotated

from crm_core.models.company import Company
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from crm_api.deps import get_vault_service

router = APIRouter()


class CompanyCreate(BaseModel):
    id: str
    name: str
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    address: str | None = None
    owner: str | None = None
    tags: list[str] = []


class CompanyUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    owner: str | None = None
    tags: list[str] | None = None


@router.get("/", response_model=list[Company])
def list_companies(
    q: Annotated[str | None, Query(description="Free-text or field:value query")] = None,
    svc: VaultService = Depends(get_vault_service),
) -> list[Company]:
    qs = QuerySet(svc.vault_root, "company", Company)
    if q:
        qs = qs.filter(q)
    return qs.all()


@router.get("/{slug}", response_model=Company)
def get_company(slug: str, svc: VaultService = Depends(get_vault_service)) -> Company:
    try:
        return svc.read("company", slug, Company)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Company '{slug}' not found") from exc


@router.post("/", response_model=Company, status_code=201)
def create_company(payload: CompanyCreate, svc: VaultService = Depends(get_vault_service)) -> Company:
    company = Company(**payload.model_dump())
    try:
        svc.create("company", company)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=f"Company '{company.id}' already exists") from exc
    return company


@router.patch("/{slug}", response_model=Company)
def update_company(
    slug: str,
    payload: CompanyUpdate,
    svc: VaultService = Depends(get_vault_service),
) -> Company:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")
    try:
        merged = svc.update("company", slug, updates)
        return Company.model_validate(merged)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Company '{slug}' not found") from exc


@router.delete("/{slug}", status_code=204)
def delete_company(slug: str, svc: VaultService = Depends(get_vault_service)) -> None:
    try:
        svc.delete("company", slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Company '{slug}' not found") from exc
