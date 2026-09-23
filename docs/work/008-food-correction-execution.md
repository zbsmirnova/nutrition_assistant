# W008 — Execute same-entry correction, delete, and restore

Status: done.
Milestone: M2.
Owner: lead assistant, architect/developer; developer verification complete.
Updated: 2026-09-23.

## Outcome and scope

Make the already-defined food correction commands executable against PostgreSQL. A correction keeps the entry identity and records a new revision; deletion removes the current entry from totals without destroying history; restore creates a new revision from a selected prior active revision. All writes are idempotent by operation and guarded by the expected current revision.

This bounded slice covers trusted `CommandEnvelope` inputs and backend arithmetic/persistence. It does not implement natural-language target resolution, ambiguous correction clarification, pending corrections, message-edit handling, or general multi-action corrections.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W008-A01 | A correction from 250 g to 80 g keeps the same entry ID, creates a second revision, recalculates nutrition, and updates the day total. |
| W008-A02 | The prior revision and component snapshot remain queryable and unchanged after correction. |
| W008-A03 | A delete creates a deleted current revision, excludes the entry from totals, and retains the prior active revision. |
| W008-A04 | A restore from a selected prior active revision creates a new revision, returns the entry to totals, and preserves the deleted/corrected history. |
| W008-A05 | A stale expected revision is rejected without changing current state, totals, or outbox rows. |
| W008-A06 | Replaying a correction, delete, or restore returns the original outcome without another revision, entry, or outbox row. |
| W008-A07 | Existing add-food, clarification, migration, ownership, arithmetic, provider, and transport checks remain green. |

## Implementation checklist

- [x] Extend FoodService validation and execution for correction/delete/restore commands.
- [x] Preserve immutable revision/component snapshots and recalculate affected day summaries.
- [x] Add PostgreSQL coverage for correction, delete, restore, stale guards, replay, and ownership.
- [x] Run offline, integration, and retained QA suites and record the exact revision.
- [x] Commit the completed slice with maintained documentation and QA evidence.

## Handoff

The implementation is committed in `36e0bf49597e295c81ee14a04948f9c3e25b1cf6`. Offline tests pass (`96`), PostgreSQL integration passes (`65`), and retained QA passes (`32`). No migration was needed. Conversation target resolution remains a follow-up after backend execution.

## QA result and completion

Developer verification passes for the trusted correction/delete/restore workflow. Evidence is in [008-food-correction-execution-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/008-food-correction-execution-developer.md?type=file&root=%252F). No independent W008 review, live Nebius, or real Telegram behavior is claimed.
