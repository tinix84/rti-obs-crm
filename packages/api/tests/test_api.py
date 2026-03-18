"""Integration tests for the FastAPI application."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crm_core.models.contact import Contact, ContactStatus
from crm_core.models.deal import Deal
from crm_core.vault.service import VaultService
from crm_api.main import app
from crm_api.deps import get_vault_service, get_vault_root


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    """Seed a temp vault with one contact and one deal."""
    svc = VaultService(tmp_path)
    svc.create(
        "contact",
        Contact(id="cnt-001", name="Alice Rossi", email="alice@acme.com", status=ContactStatus.CUSTOMER),
    )
    svc.create(
        "deal",
        Deal(id="deal-001", title="Big Deal", stage="proposal", value=10000.0, probability=0.50),
    )
    return tmp_path


@pytest.fixture
def client(vault_dir: Path) -> TestClient:
    """TestClient with the vault DI overridden to use a temp directory."""
    app.dependency_overrides[get_vault_service] = lambda: VaultService(vault_dir)
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Contacts ──────────────────────────────────────────────────────────────────

def test_list_contacts(client: TestClient) -> None:
    r = client.get("/contacts/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice Rossi"


def test_get_contact_found(client: TestClient) -> None:
    r = client.get("/contacts/alice-rossi")
    assert r.status_code == 200
    assert r.json()["id"] == "cnt-001"


def test_get_contact_not_found(client: TestClient) -> None:
    r = client.get("/contacts/nobody")
    assert r.status_code == 404


def test_create_contact(client: TestClient) -> None:
    payload = {"id": "cnt-002", "name": "Bruno Ferrari", "email": "b@startup.io"}
    r = client.post("/contacts/", json=payload)
    assert r.status_code == 201
    assert r.json()["name"] == "Bruno Ferrari"


def test_create_contact_conflict(client: TestClient) -> None:
    payload = {"id": "cnt-001", "name": "Alice Rossi"}
    r = client.post("/contacts/", json=payload)
    assert r.status_code == 409


def test_update_contact(client: TestClient) -> None:
    r = client.patch("/contacts/alice-rossi", json={"status": "churned"})
    assert r.status_code == 200
    assert r.json()["status"] == "churned"


def test_delete_contact(client: TestClient) -> None:
    r = client.delete("/contacts/alice-rossi")
    assert r.status_code == 204
    r2 = client.get("/contacts/alice-rossi")
    assert r2.status_code == 404


def test_search_contacts(client: TestClient) -> None:
    r = client.get("/contacts/?q=Alice")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ── Deals ─────────────────────────────────────────────────────────────────────

def test_list_deals(client: TestClient) -> None:
    r = client.get("/deals/")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_deal_not_found(client: TestClient) -> None:
    r = client.get("/deals/nonexistent")
    assert r.status_code == 404


# ── Metrics ───────────────────────────────────────────────────────────────────

def test_metrics_endpoint(client: TestClient) -> None:
    r = client.get("/metrics/")
    assert r.status_code == 200
    body = r.json()
    assert body["total_deals"] == 1
    assert body["total_pipeline_value"] == 10000.0
    assert body["total_forecast_value"] == 5000.0
    assert "proposal" in body["funnel_count"]
