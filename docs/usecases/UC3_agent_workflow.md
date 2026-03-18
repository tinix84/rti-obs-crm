# UC3 – Agent Workflow Orchestration (DAG)
**Epic**: Define, validate, and execute multi-step CRM workflows as Directed Acyclic Graphs.

## Context
Workflows encode business rules without requiring LLM for routing. A workflow is
described in a YAML file and converted at runtime to a `networkx.DiGraph`. Each node is
a typed step (action, condition, delay, notification). The engine executes them in
topological order and persists execution state in the vault.

## Actors
- **DAG Engine** (runtime executor)
- **Workflow Definition** (YAML config authored by user/dev)
- **Vault Service** (state persistence)
- **External triggers** (deal stage change, new contact, scheduled cron)

## User Stories
| ID | Story | Priority |
|----|-------|----------|
| US-13 | As a dev I want to define a workflow in YAML without writing Python | Must |
| US-14 | As the engine I want to validate a workflow DAG (no cycles, all nodes reachable) | Must |
| US-15 | As the engine I want to execute nodes in topological order | Must |
| US-16 | As a user I want to see execution history logged in the vault as a note | Should |
| US-17 | As a dev I want conditional branching based on vault frontmatter values | Should |
| US-18 | As a dev I want to register custom node types via plugin | Could |

## Acceptance Criteria
- DAG validation rejects cyclic graphs with descriptive error
- Topological execution order guaranteed by `networkx.topological_sort`
- Execution log written to `vault/workflows/runs/<workflow_id>/<run_id>.md`
- Condition nodes evaluate Python expressions against frontmatter dict (sandboxed `eval`)
- At least two built-in workflows: `on_deal_won` and `new_lead_nurture`

## Out of Scope
- Distributed execution (single-process for now)
- UI workflow builder (future epic)
