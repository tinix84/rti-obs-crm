# UC2 – Deal / Pipeline Tracking
**Epic**: Track sales opportunities through a configurable pipeline.

## Context
Deals (opportunities) represent potential revenue. Each deal is a `.md` note linked to
a contact and optionally a company. The pipeline stages are configurable via a
`config/pipeline.yaml` file; no code change required to add stages.

## Actors
- **User** (sales rep / manager)
- **Vault Service**
- **DAG Engine** (automated stage transitions and notifications)
- **API / Bot**

## User Stories
| ID | Story | Priority |
|----|-------|----------|
| US-07 | As a user I want to create a deal linked to a contact | Must |
| US-08 | As a user I want to move a deal across pipeline stages (Kanban view) | Must |
| US-09 | As a user I want to see deal value, close date, and probability | Must |
| US-10 | As a user I want the system to trigger a DAG workflow when a deal is Won | Should |
| US-11 | As a manager I want a revenue forecast based on stage × probability (no LLM) | Should |
| US-12 | As an API consumer I want CRUD operations on deals | Could |

## Acceptance Criteria
- Deal frontmatter: `id`, `title`, `contact_id`, `company_id`, `stage`, `value`, `currency`, `probability`, `close_date`, `owner`, `tags`, `created_at`, `updated_at`
- `stage` validated against `config/pipeline.yaml`
- DAG workflow `on_deal_won` fires when stage transitions to `Won`
- Forecast = `SUM(value * probability)` computed with plain arithmetic (no LLM)

## Out of Scope
- Contract generation, e-signature (future epics)
