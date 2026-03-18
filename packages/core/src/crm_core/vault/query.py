"""Vault query engine – no LLM, pure regex + field matching.

Supports two query styles:
1. Free-text search: matched against all string frontmatter values with regex.
2. Structured field queries: ``status:customer``, ``stage:Won``, ``tag:vip``.

Example::

    qs = QuerySet(vault_root, "contact", Contact)
    results = qs.filter("alice").filter_field("status", "customer").all()
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from crm_core.vault import parser

T = TypeVar("T", bound=BaseModel)

_FIELD_QUERY = re.compile(r"^(?P<field>\w+):(?P<value>.+)$")


def _matches_text(meta: dict[str, Any], pattern: re.Pattern) -> bool:
    """Return True if any string value in *meta* matches *pattern*."""
    for v in meta.values():
        if isinstance(v, str) and pattern.search(v):
            return True
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and pattern.search(item):
                    return True
    return False


def _matches_field(meta: dict[str, Any], field: str, value: str) -> bool:
    """Return True if meta[field] equals value or contains value (for lists)."""
    actual = meta.get(field)
    if actual is None:
        return False
    if isinstance(actual, list):
        return value in actual
    return str(actual).lower() == value.lower()


class QuerySet:
    """Lazy, chainable query builder over a vault entity directory."""

    def __init__(self, vault_root: Path, entity_type: str, model_cls: type[T]) -> None:
        from crm_core.vault.service import SUBDIR

        self._vault_root = vault_root
        self._entity_type = entity_type
        self._model_cls = model_cls
        sub = SUBDIR.get(entity_type, entity_type)
        self._directory = vault_root / sub
        self._text_filters: list[re.Pattern] = []
        self._field_filters: list[tuple[str, str]] = []

    # ── filter builders (chainable) ───────────────────────────────────────

    def filter(self, query: str) -> QuerySet:
        """Add a free-text filter (case-insensitive regex).

        If *query* looks like ``field:value`` it is treated as a field filter
        instead.
        """
        m = _FIELD_QUERY.match(query.strip())
        if m:
            return self.filter_field(m.group("field"), m.group("value"))
        self._text_filters.append(re.compile(re.escape(query), re.IGNORECASE))
        return self

    def filter_field(self, field: str, value: str) -> QuerySet:
        """Add a structured field filter."""
        self._field_filters.append((field, value))
        return self

    # ── materialise ──────────────────────────────────────────────────────

    def _iter_meta(self) -> Iterator[tuple[Path, dict[str, Any]]]:
        if not self._directory.exists():
            return
        for md_file in sorted(self._directory.glob("*.md")):
            try:
                meta, _ = parser.load(md_file)
            except Exception:
                continue
            yield md_file, meta

    def all(self) -> list[T]:
        """Return all matching models."""
        import logging

        log = logging.getLogger(__name__)
        results: list[T] = []
        for path, meta in self._iter_meta():
            if not all(_matches_text(meta, p) for p in self._text_filters):
                continue
            if not all(_matches_field(meta, f, v) for f, v in self._field_filters):
                continue
            try:
                results.append(self._model_cls.model_validate(meta))
            except Exception as exc:
                log.warning("Skipping %s: %s", path.name, exc)
        return results

    def count(self) -> int:
        """Return the number of matching records."""
        return len(self.all())
