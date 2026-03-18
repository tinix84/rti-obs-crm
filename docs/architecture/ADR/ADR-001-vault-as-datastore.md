# ADR-001: Use Obsidian Vault as the Primary Data Store

**Date**: 2026-03-18
**Status**: Accepted

## Context
The CRM needs a data store that is human-readable, easy to edit without special tools,
and usable directly inside Obsidian (the user's preferred knowledge management tool).

## Decision
All CRM entities (contacts, deals, companies, tasks) are stored as Markdown files with
YAML frontmatter inside an Obsidian vault. The frontmatter acts as the structured
metadata layer; the Markdown body holds free-form notes.

## Consequences
+ No database server to manage; works offline.
+ Full git history of all CRM data.
+ Obsidian's link graph shows relationships visually.
+ Users can edit notes directly in Obsidian.
− Concurrent writes require file-level locking (mitigated by atomic rename).
− Querying requires scanning files (mitigated by DuckDB shadow DB).
