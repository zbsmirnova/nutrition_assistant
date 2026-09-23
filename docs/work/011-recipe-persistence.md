# W011 — Recipe persistence and immutable versions

Status: in progress.
Milestone: M3.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D021.

## Outcome and scope

Persist user recipe definitions and revisions using the existing typed command boundary. Keep original ingredient quantities/instructions, persist per-100-g nutrition and calculation provenance, calculate resolved recipes in the backend, and expose current recipe retrieval. Runtime general-database comparison and recipe consumption are outside this slice.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W011-A01 | `define_recipe` persists one recipe identity, version, original ingredient snapshots, instructions, and per-100-g profile. |
| W011-A02 | Calculated recipes use pinned product nutrition and normalized mass sources; unknown nutrients remain unknown and model-computed totals are ignored. |
| W011-A03 | `revise_recipe` creates a new immutable version and rejects a stale expected version. |
| W011-A04 | Retrieval returns the current version and preserves earlier history; cross-user sources and recipe IDs are rejected. |
| W011-A05 | Migration, offline, integration, retained QA, and schema-drift checks pass. |

## Boundaries

The service does not yet interpret natural-language recipe messages, search recipes, consume recipe grams in food entries, resolve volume density, compare against an external general database, or render recipe Telegram replies.
