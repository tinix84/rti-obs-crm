"""Low-level markdown + YAML-frontmatter parser.

Uses python-frontmatter for parsing and rendering.  Writes are atomic
(write to temp file → rename) to avoid partial-write corruption.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import frontmatter  # python-frontmatter


def load(path: Path) -> tuple[dict[str, Any], str]:
    """Parse a markdown file; return (frontmatter_dict, body_text).

    Raises FileNotFoundError if path does not exist.
    """
    post = frontmatter.load(str(path))
    return dict(post.metadata), post.content


def dump(path: Path, metadata: dict[str, Any], body: str) -> None:
    """Write metadata + body back to a markdown file atomically.

    The file is written to a sibling temp file first, then renamed, so
    the original is never half-written.
    """
    post = frontmatter.Post(body, **metadata)
    content = frontmatter.dumps(post)

    dir_ = path.parent
    dir_.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp.md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def update_frontmatter(path: Path, updates: dict[str, Any]) -> dict[str, Any]:
    """Load a note, merge *updates* into its frontmatter, and save it.

    Returns the merged frontmatter dict.
    """
    meta, body = load(path)
    meta.update(updates)
    dump(path, meta, body)
    return meta
