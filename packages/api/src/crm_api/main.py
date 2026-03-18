"""FastAPI application entry point."""

from __future__ import annotations

import os

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

# CORS: defaults to localhost dev origins; override with CORS_ORIGINS env var.
# In production, set CORS_ORIGINS to your frontend URL(s).
# Example: CORS_ORIGINS="https://crm.example.com,https://app.example.com"
_cors_env = os.environ.get("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000")
_allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
app.include_router(deals.router, prefix="/deals", tags=["Deals"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok"}
