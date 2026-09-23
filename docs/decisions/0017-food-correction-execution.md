# D017 — Execute same-entry food corrections, deletion, and restore

Kind: technical
Status: accepted for W008
Recorded: 2026-09-23.
Decision owner: architect under the accepted FOOD-003 and DATA-002 requirements.
Acceptance evidence: the typed command contract already defines complete replacement, deletion, and restoration commands with expected revision guards. This record fixes their first executable backend boundary.

## Decision

Implement W008 as a stateful FoodService slice:

- A correction keeps the existing `food_entry_id`, creates a new immutable revision, recalculates each replacement component from its pinned product version, and moves the current pointer to the new revision.
- A deletion also creates a new revision with `state=deleted`; it removes the entry from current day totals while preserving the prior active revision and its components.
- A restore creates a new active revision by copying a selected prior active revision. The command must identify the current revision it expects and the historical revision to restore.
- Every state-changing command is protected by the existing user-row lock and `expected_revision_id`. A stale target raises a conflict and leaves the current entry, totals, revisions, and response outbox unchanged.
- If a correction or restore moves an entry to another local date, both source and destination day revisions are updated and both summaries are returned. Day completeness is preserved; an active mutation clears only the explicit-zero marker on a touched day.
- Operation replay returns the stored outcome. Distinct correction, delete, or restore messages have distinct operation identities and therefore remain independently auditable.

This slice executes trusted typed commands. It does not claim that the conversational worker can yet resolve arbitrary correction targets, parse natural-language undo/delete, or answer an ambiguous correction.

## Alternatives and consequences

Mutating the current revision in place would lose the required correction history and make undo dependent on an external message log. Reusing the original add operation would break idempotency and response provenance. Requiring the expected current revision makes concurrent or delayed corrections visible instead of silently overwriting a newer user change.

## References

FOOD-003, DATA-002, DATA-003 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F); [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); and [008-food-correction-execution.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/008-food-correction-execution.md?type=file&root=%252F).
