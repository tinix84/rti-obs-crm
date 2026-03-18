"""Tests for vault parser (frontmatter CRUD)."""

import os
import tempfile
from pathlib import Path

import pytest

from crm_core.vault import parser


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    return tmp_path


def test_dump_and_load_roundtrip(tmp_vault: Path) -> None:
    path = tmp_vault / "test-note.md"
    meta = {"id": "cnt-001", "name": "Alice", "status": "lead", "tags": ["vip"]}
    body = "## Notes\nHello world"

    parser.dump(path, meta, body)

    loaded_meta, loaded_body = parser.load(path)
    assert loaded_meta["id"] == "cnt-001"
    assert loaded_meta["name"] == "Alice"
    assert loaded_meta["status"] == "lead"
    assert "Hello world" in loaded_body


def test_dump_creates_parent_dirs(tmp_vault: Path) -> None:
    path = tmp_vault / "contacts" / "alice.md"
    parser.dump(path, {"id": "cnt-001"}, "")
    assert path.exists()


def test_update_frontmatter_preserves_body(tmp_vault: Path) -> None:
    path = tmp_vault / "note.md"
    parser.dump(path, {"id": "1", "status": "lead"}, "## Body text remains intact")

    parser.update_frontmatter(path, {"status": "customer"})

    meta, body = parser.load(path)
    assert meta["status"] == "customer"
    assert "Body text remains intact" in body


def test_load_missing_file_raises(tmp_vault: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parser.load(tmp_vault / "nonexistent.md")


def test_dump_is_atomic(tmp_vault: Path) -> None:
    """No temp files should survive after a successful write."""
    path = tmp_vault / "atomic.md"
    parser.dump(path, {"id": "1"}, "")
    tmp_files = list(tmp_vault.glob("*.tmp.md"))
    assert len(tmp_files) == 0
