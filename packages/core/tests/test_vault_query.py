"""Tests for vault QuerySet (no-LLM search)."""

from pathlib import Path

import pytest

from crm_core.models.contact import Contact, ContactStatus
from crm_core.vault.query import QuerySet
from crm_core.vault.service import VaultService


@pytest.fixture
def vault_with_contacts(tmp_path: Path) -> Path:
    svc = VaultService(tmp_path)
    svc.create(
        "contact",
        Contact(id="cnt-001", name="Alice Rossi", email="alice@acme.com", status=ContactStatus.CUSTOMER, tags=["vip"]),
    )
    svc.create(
        "contact",
        Contact(id="cnt-002", name="Bruno Ferrari", email="bferrari@startup.io", status=ContactStatus.LEAD),
    )
    svc.create(
        "contact",
        Contact(id="cnt-003", name="Carla Bianchi", email="cbianchi@corp.com", status=ContactStatus.CUSTOMER),
    )
    return tmp_path


def test_filter_free_text(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter("Alice").all()
    assert len(results) == 1
    assert results[0].name == "Alice Rossi"


def test_filter_free_text_case_insensitive(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter("alice").all()
    assert len(results) == 1


def test_filter_structured_field(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter_field("status", "customer").all()
    assert len(results) == 2
    assert all(c.status == ContactStatus.CUSTOMER for c in results)


def test_filter_shorthand_syntax(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter("status:lead").all()
    assert len(results) == 1
    assert results[0].name == "Bruno Ferrari"


def test_filter_by_tag(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter_field("tags", "vip").all()
    assert len(results) == 1
    assert results[0].name == "Alice Rossi"


def test_chained_filters(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    results = qs.filter("status:customer").filter("Alice").all()
    assert len(results) == 1


def test_count(vault_with_contacts: Path) -> None:
    qs = QuerySet(vault_with_contacts, "contact", Contact)
    assert qs.count() == 3


def test_empty_vault(tmp_path: Path) -> None:
    qs = QuerySet(tmp_path, "contact", Contact)
    assert qs.all() == []
