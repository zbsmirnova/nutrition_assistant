# W008 — Execute same-entry correction, delete, and restore

Status: in progress.
Milestone: M2.
Owner: lead assistant, architect/developer; independent QA pending.
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

- [ ] Extend FoodService validation and execution for correction/delete/restore commands.
- [ ] Preserve immutable revision/component snapshots and recalculate affected day summaries.
- [ ] Add PostgreSQL coverage for correction, delete, restore, stale guards, replay, and ownership.
- [ ] Run offline, integration, and retained QA suites and record the exact revision.
- [ ] Commit the completed slice with maintained documentation and QA evidence.

## Handoff

The typed contracts and database schema already contain the command and revision shapes. No migration is expected for this slice. Conversation target resolution remains a follow-up after backend execution is verified.
