"""Tests for VaultService CRUD operations."""

from pathlib import Path

import pytest

from crm_core.models.contact import Contact, ContactStatus
from crm_core.models.deal import Deal
from crm_core.vault.service import VaultService


@pytest.fixture
def vault(tmp_path: Path) -> VaultService:
    return VaultService(tmp_path)


def _make_contact(id_: str = "cnt-001", name: str = "Alice Rossi") -> Contact:
    return Contact(id=id_, name=name, email="alice@example.com", status=ContactStatus.LEAD)


def test_create_and_read(vault: VaultService) -> None:
    contact = _make_contact()
    path = vault.create("contact", contact, body="## Notes\nTest")
    assert path.exists()

    loaded = vault.read("contact", "alice-rossi", Contact)
    assert loaded.id == "cnt-001"
    assert loaded.name == "Alice Rossi"
    assert loaded.status == ContactStatus.LEAD


def test_create_raises_if_exists(vault: VaultService) -> None:
    contact = _make_contact()
    vault.create("contact", contact)
    with pytest.raises(FileExistsError):
        vault.create("contact", _make_contact())


def test_update_field(vault: VaultService) -> None:
    vault.create("contact", _make_contact())
    vault.update("contact", "alice-rossi", {"status": "customer"})
    loaded = vault.read("contact", "alice-rossi", Contact)
    assert loaded.status == ContactStatus.CUSTOMER


def test_delete_moves_to_trash(vault: VaultService) -> None:
    vault.create("contact", _make_contact())
    trash_path = vault.delete("contact", "alice-rossi")
    assert trash_path.exists()
    assert not (vault.vault_root / "contacts" / "alice-rossi.md").exists()


def test_delete_missing_raises(vault: VaultService) -> None:
    with pytest.raises(FileNotFoundError):
        vault.delete("contact", "nonexistent")


def test_list_all_yields_models(vault: VaultService) -> None:
    vault.create("contact", _make_contact("cnt-001", "Alice"))
    vault.create("contact", _make_contact("cnt-002", "Bruno Ferrari"))
    contacts = list(vault.list_all("contact", Contact))
    names = {c.name for c in contacts}
    assert "Alice" in names
    assert "Bruno Ferrari" in names


def test_list_all_empty_directory(vault: VaultService) -> None:
    contacts = list(vault.list_all("contact", Contact))
    assert contacts == []


def test_deal_create_and_read(vault: VaultService) -> None:
    deal = Deal(id="deal-001", title="Big Deal", stage="lead", value=10000.0)
    vault.create("deal", deal)
    loaded = vault.read("deal", "big-deal", Deal)
    assert loaded.id == "deal-001"
    assert loaded.value == 10000.0
