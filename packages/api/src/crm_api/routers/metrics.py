"""Metrics router – pipeline funnel and revenue forecast (no LLM)."""

from __future__ import annotations

from crm_core.models.deal import Deal
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService
from fastapi import APIRouter, Depends

from crm_api.deps import get_vault_service

router = APIRouter()


@router.get("/")
def get_metrics(svc: VaultService = Depends(get_vault_service)) -> dict:
    """Return pipeline funnel counts and weighted revenue forecast."""
    deals = QuerySet(svc.vault_root, "deal", Deal).all()

    funnel: dict[str, int] = {}
    forecast: dict[str, float] = {}

    for deal in deals:
        funnel[deal.stage] = funnel.get(deal.stage, 0) + 1
        forecast[deal.stage] = round(forecast.get(deal.stage, 0.0) + deal.weighted_value, 2)

    total_pipeline = sum(d.value for d in deals)
    total_forecast = sum(d.weighted_value for d in deals)

    return {
        "total_deals": len(deals),
        "total_pipeline_value": round(total_pipeline, 2),
        "total_forecast_value": round(total_forecast, 2),
        "funnel_count": funnel,
        "funnel_forecast": forecast,
    }
