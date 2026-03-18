# UC1 – Contact Management
**Epic**: Manage individual contact records stored as Obsidian notes.

## Context
A user (sales rep or account manager) needs to create, update, and search contact
records without leaving Obsidian. Each contact is a single `.md` file with YAML
frontmatter acting as the structured metadata layer.

## Actors
- **User** (sales rep / account manager)
- **Vault Service** (reads/writes frontmatter – no LLM involved)
- **API** (optional programmatic access)

## User Stories
| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a user I want to create a new contact note with pre-filled template so I don't forget required fields | Must |
| US-02 | As a user I want to search contacts by name, company, or tag using plain-text query so I get fast results | Must |
| US-03 | As a user I want to update a contact's status (lead / prospect / customer / churned) | Must |
| US-04 | As a user I want to link a contact to a company note with a wikilink | Should |
| US-05 | As a user I want to see the full interaction timeline (notes sorted by date) | Should |
| US-06 | As a bot/API I want to create or update a contact via REST or MCP tool | Could |

## Acceptance Criteria
- Every contact note contains `id`, `name`, `email`, `status`, `company`, `tags`, `created_at`, `updated_at` in frontmatter
- `status` follows the enum: `lead | prospect | customer | churned`
- Vault service parses/writes frontmatter without corrupting existing markdown body
- Search is performed with regex/YAML-query (no LLM)
- Round-trip test: create → read → update → delete leaves vault consistent

## Out of Scope
- Email sending, calendar integration (separate epics)
- Duplicate detection (separate epic)
