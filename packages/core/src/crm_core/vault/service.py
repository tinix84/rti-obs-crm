"""High-level CRUD service for Obsidian vault notes.

Each entity type (Contact, Deal, Company, Task) lives in its own sub-directory.
The service handles:
- create: write a new note from a Pydantic model
- read:   parse a note and return a Pydantic model
- update: merge new field values into the frontmatter
- delete: move the note to <vault>/.trash/
- list:   yield all models of a given type
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from crm_core.vault import parser

T = TypeVar("T", bound=BaseModel)

# Sub-directory names inside the vault root
SUBDIR = {
    "contact": "contacts",
    "deal": "deals",
    "company": "companies",
    "task": "tasks",
}


class VaultService:
    """CRUD operations on vault markdown notes.

    Parameters
    ----------
    vault_root:
        Absolute path to the Obsidian vault directory.
    """

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = Path(vault_root)

    # ── helpers ──────────────────────────────────────────────────────────

    def _dir(self, entity_type: str) -> Path:
        sub = SUBDIR.get(entity_type, entity_type)
        return self.vault_root / sub

    def _path(self, entity_type: str, slug: str) -> Path:
        return self._dir(entity_type) / f"{slug}.md"

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert a display name to a filesystem-safe slug."""
        import re

        slug = text.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    # ── CRUD ─────────────────────────────────────────────────────────────

    def create(self, entity_type: str, model: T, body: str = "") -> Path:
        """Write a new vault note from a Pydantic model.

        Returns the path of the created file.
        Raises FileExistsError if the note already exists.
        """
        meta = model.to_frontmatter()  # type: ignore[attr-defined]
        slug = self._slugify(str(getattr(model, "name", getattr(model, "title", model.id))))  # type: ignore[attr-defined]
        path = self._path(entity_type, slug)
        if path.exists():
            raise FileExistsError(f"Vault note already exists: {path}")
        parser.dump(path, meta, body)
        return path

    def read(self, entity_type: str, slug: str, model_cls: type[T]) -> T:
        """Read a vault note and return a validated Pydantic model.

        Raises FileNotFoundError if the note does not exist.
        """
        path = self._path(entity_type, slug)
        meta, _ = parser.load(path)
        return model_cls.model_validate(meta)

    def read_path(self, path: Path, model_cls: type[T]) -> T:
        """Read an arbitrary vault note by absolute path."""
        meta, _ = parser.load(path)
        return model_cls.model_validate(meta)

    def update(self, entity_type: str, slug: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update frontmatter fields in an existing note.

        Automatically sets ``updated_at`` to the current UTC time.
        Enum values are converted to their string representation before writing.
        Returns the merged frontmatter dict.
        """
        from enum import Enum

        updates["updated_at"] = datetime.now(UTC).isoformat()
        # Ensure all values are YAML-serialisable (convert enums to their .value)
        serialisable = {k: (v.value if isinstance(v, Enum) else v) for k, v in updates.items()}
        path = self._path(entity_type, slug)
        return parser.update_frontmatter(path, serialisable)

    def delete(self, entity_type: str, slug: str) -> Path:
        """Move a vault note to <vault>/.trash/.

        Returns the path the note was moved to.
        Raises FileNotFoundError if the note does not exist.
        """
        src = self._path(entity_type, slug)
        if not src.exists():
            raise FileNotFoundError(f"Vault note not found: {src}")
        trash = self.vault_root / ".trash" / entity_type
        trash.mkdir(parents=True, exist_ok=True)
        dst = trash / src.name
        shutil.move(str(src), str(dst))
        return dst

    def list_all(self, entity_type: str, model_cls: type[T]) -> Iterator[T]:
        """Yield all validated models for the given entity type.

        Notes that fail validation are skipped with a warning log.
        """
        import logging

        log = logging.getLogger(__name__)
        directory = self._dir(entity_type)
        if not directory.exists():
            return
        for md_file in sorted(directory.glob("*.md")):
            try:
                meta, _ = parser.load(md_file)
                yield model_cls.model_validate(meta)
            except Exception as exc:
                log.warning("Skipping %s: %s", md_file.name, exc)
