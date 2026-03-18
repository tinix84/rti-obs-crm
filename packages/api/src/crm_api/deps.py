"""Dependency injection helpers for FastAPI routes."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from crm_core.dag.engine import DAGEngine
from crm_core.vault.service import VaultService


@lru_cache
def get_vault_root() -> Path:
    """Return the vault root path from the environment (or a sensible default)."""
    env = os.environ.get("VAULT_ROOT")
    if env:
        return Path(env).resolve()
    # Default: look for vault/ relative to the project root
    candidate = Path(__file__).parent.parent.parent.parent.parent.parent / "vault"
    if candidate.exists():
        return candidate
    raise RuntimeError(
        "VAULT_ROOT environment variable is not set and vault/ directory not found. "
        "Set VAULT_ROOT to the absolute path of your Obsidian vault."
    )


def get_vault_service() -> VaultService:
    return VaultService(get_vault_root())


@lru_cache
def get_dag_engine() -> DAGEngine:
    engine = DAGEngine(vault_root=get_vault_root())
    workflows_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "config" / "workflows"
    if workflows_dir.exists():
        engine.load_from_directory(workflows_dir)
    return engine
