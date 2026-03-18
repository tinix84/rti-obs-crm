"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crm_api.routers import companies, contacts, deals, metrics, workflows

app = FastAPI(
    title="RTI Obs CRM API",
    description="REST interface for the Obsidian-backed CRM system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
app.include_router(deals.router, prefix="/deals", tags=["Deals"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok"}
