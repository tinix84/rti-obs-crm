# ADR-002: Prefer Regex/Queries over LLM for Structured Operations

**Date**: 2026-03-18
**Status**: Accepted

## Context
Many CRM operations (search, filter, CRUD) can be performed deterministically with
structured queries. Using an LLM for these operations adds latency, cost, and
non-determinism without benefit.

## Decision
All CRUD, search, and analytics operations use Python (regex, YAML parsing, pandas,
DuckDB SQL). LLM is invoked **only** for genuinely generative tasks:
- Summarizing free-text contact notes
- Drafting follow-up email suggestions
- Classifying unstructured input from external sources

## Consequences
+ Dramatically lower latency (< 100 ms vs 1–5 s for LLM calls).
+ Zero API cost for the majority of operations.
+ Deterministic, testable behaviour.
+ Easier to debug (no prompt engineering).
− Less "magic" for operations that could benefit from NLP (acceptable trade-off).
