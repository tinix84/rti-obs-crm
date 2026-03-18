# UC5 – Reporting & Analytics
**Epic**: Provide summary metrics and dashboards computed from vault frontmatter without LLM.

## Context
All CRM metrics are derived by parsing YAML frontmatter from the vault and computing
aggregations with plain Python/pandas. No LLM needed for counts, sums, or pivot tables.
A Streamlit page provides a live dashboard; a REST endpoint serves the same data as JSON.

## Actors
- **User** (manager / executive)
- **Vault Service** (data source)
- **Streamlit UI** (dashboard)
- **API** (data export)

## User Stories
| ID | Story | Priority |
|----|-------|----------|
| US-25 | As a manager I want a pipeline funnel chart (count per stage) | Must |
| US-26 | As a manager I want revenue forecast (value × probability per stage) | Must |
| US-27 | As a manager I want lead conversion rate (leads → customers) | Should |
| US-28 | As a user I want to export contacts/deals to CSV | Should |
| US-29 | As an API consumer I want `/metrics` endpoint returning JSON summary | Could |

## Acceptance Criteria
- All metrics computed with `pandas` groupby / sum (no LLM)
- Streamlit dashboard refreshes on vault file changes (using `st.cache_data` + TTL)
- CSV export includes all frontmatter fields
- `/metrics` endpoint returns pipeline funnel and forecast in < 200 ms for vault ≤ 1000 notes

## Out of Scope
- Real-time streaming metrics
- External BI tool connectors
