# ADR-003: Use networkx for DAG Workflow Engine

**Date**: 2026-03-18
**Status**: Accepted

## Context
Workflow orchestration requires directed acyclic graph execution with topological sort,
cycle detection, and node metadata. Several options exist: LangGraph, Prefect, Airflow,
or plain networkx.

## Decision
Use `networkx` directly for the DAG engine. Workflows are defined in YAML and
loaded into `networkx.DiGraph` at runtime. Execution is single-process and synchronous
(async support can be added later).

## Rationale
- LangGraph and similar frameworks are designed for LLM chains – overkill and opinionated.
- Prefect/Airflow require external services (database, scheduler).
- `networkx` is a pure-Python library with zero external dependencies, perfect for
  embedding in the core package.

## Consequences
+ Lightweight, no external services.
+ Full control over execution model.
+ Easy to test (deterministic graph algorithms).
− No built-in scheduler (use system cron or APScheduler if needed).
− No distributed execution (single-process; acceptable for local-first CRM).
