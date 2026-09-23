# W010 — Entry target selection and correction fields

Status: in progress.
Milestone: M2.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.

## Outcome and scope

Extend W009's bounded food-entry targeting with durable numbered disambiguation and same-entry date/meal corrections. The parser still proposes actions; the backend resolves opaque references, validates evidence, and executes guarded commands.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W010-A01 | An ambiguous description creates pending numbered selection candidates and no mutation. |
| W010-A02 | A valid selection reply resumes the original correction/delete/undo operation, updates only the selected entry, and replays idempotently. |
| W010-A03 | Date correction moves one entry across day summaries; meal correction revises the same day and preserves entry identity/history. |
| W010-A04 | Parser context exposes only opaque entry metadata; pending action/evidence linkage is retained in the trusted command. |
| W010-A05 | Existing offline, integration, provider, transport, migration, and QA checks remain green; generated schemas are current. |

## Implementation checklist

- [x] Add `set_meal` and use the existing `move_date` parser change.
- [x] Persist pending entry candidates and validate selection answers.
- [x] Permit trusted correction resumption with original plus answer evidence.
- [x] Add integration coverage for ambiguous selection, date move, meal change, and replay.
- [ ] Run PostgreSQL integration and retained QA suites; record exact revision.
- [ ] Commit the completed implementation and evidence slices.

## Boundaries

This slice does not implement arbitrary target search, multi-component correction, message edits, live Telegram rendering of choice buttons, or live Nebius quality. Numbered choices are represented in durable pending context; transport presentation remains a later integration concern.
