"""Vault indexer – builds / refreshes DuckDB shadow database from frontmatter.

Run via:
    python -m crm_core.vault.index <vault_path> [--db data/crm.duckdb]

The shadow DB provides fast analytical queries (forecasts, funnels) without
scanning markdown files on every request.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import pandas as pd

from crm_core.models.company import Company
from crm_core.models.contact import Contact
from crm_core.models.deal import Deal
from crm_core.models.task import Task
from crm_core.vault.service import VaultService

log = logging.getLogger(__name__)


def build_index(vault_root: Path, db_path: Path) -> None:
    """Read all vault notes and upsert into DuckDB tables."""
    vault = VaultService(vault_root)

    contacts = [c.model_dump(mode="json") for c in vault.list_all("contact", Contact)]
    deals = [d.model_dump(mode="json") for d in vault.list_all("deal", Deal)]
    companies = [c.model_dump(mode="json") for c in vault.list_all("company", Company)]
    tasks = [t.model_dump(mode="json") for t in vault.list_all("task", Task)]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))

    for table, rows in [
        ("contacts", contacts),
        ("deals", deals),
        ("companies", companies),
        ("tasks", tasks),
    ]:
        if not rows:
            log.info("No records for table %s – skipping.", table)
            continue
        df = pd.DataFrame(rows)
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.register("_tmp_df", df)
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM _tmp_df")
        con.unregister("_tmp_df")
        log.info("Indexed %d records into table '%s'.", len(rows), table)

    con.close()
    log.info("Shadow DB written to %s", db_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Build DuckDB shadow database from vault")
    parser.add_argument("vault", type=Path, help="Path to Obsidian vault root")
    parser.add_argument("--db", type=Path, default=Path("data/crm.duckdb"), help="Output DuckDB path")
    args = parser.parse_args()
    build_index(args.vault, args.db)


if __name__ == "__main__":
    main()
