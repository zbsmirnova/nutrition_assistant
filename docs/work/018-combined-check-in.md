# W018 — Combined completion/activity check-in

Status: ready.
Milestone: M5 (depends on M4 observations, done in W017).
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D030 (behavior), under DAY-001 and D001; open technical mechanics noted below.

## Outcome and scope

Offer a single combined completion/activity check-in per local day and act on the user's choice. Behavior is fixed by D030: the offer is bundled into the dinner acknowledgment when a dinner is recognized; otherwise it is offered at 21:00 local and skipped if that moment passed while offline; the buttons are "Everything logged", "Add steps", and "Later"; "Later" dismisses without rescheduling; "Add steps" asks for steps in-flow and records a daily-steps observation via W017; and the completion action is suppressed after conversational closure or explicit completion, with a fallback-then-late-dinner and post-closure late food never creating a second logical offer.

## Requirements and decisions

DAY-001; D001 (optional completion, 21:00 fallback); D030 (this slice's behavior); section 9 of the data model (`daily_check_ins`, `notification_rules`, `notification_runs`, scheduled outbox). W017/D029 provide the steps observation the "Add steps" path reuses.

Dependencies that are technical decisions for this slice (not yet built):

- Telegram transport must gain inline-keyboard sends and `callback_query` ingress with `answerCallbackQuery`; the current transport only sends plain text and ignores non-text updates.
- A local-time scheduler must resolve the 21:00 fallback occurrence per user time zone (with DST) and create exactly one logical offer, distinct from worker attempts, without resending after edits.
- Scheduled/offer outgoing messages are not tied to an `applied_operations` row; the current `outbox` is. Section 9's `outbox_messages`/notification-run model or an equivalent must be introduced.

These mechanics are unresolved technical design and should be recorded in a follow-up technical decision before implementation; the user-facing behavior itself is settled by D030.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W018-A01 | A recognized dinner produces one outgoing message combining the acknowledgment and the check-in offer with the three actions. |
| W018-A02 | With no dinner, exactly one fallback offer is created at 21:00 local; if that time passed while offline, no offer is created for that day. |
| W018-A03 | "Everything logged" marks the day complete; "Add steps" records the day's steps as an observation; "Later" dismisses without reschedule. |
| W018-A04 | One logical offer per local day across retries and races; a fallback followed by a later dinner does not create a second offer. |
| W018-A05 | After closure or completion the completion action is suppressed; late food additions keep the day complete with no new check-in. |
| W018-A06 | Old or superseded callbacks validate current state and their bound local date; ambiguous sends are visible and not blindly duplicated. |

## Implementation checklist

Not started. Ordering proposal: (1) technical decision for transport callbacks + scheduler + scheduled-outbox model; (2) migration for `daily_check_ins` and notification tables; (3) offer lifecycle service (plan/attach/dismiss/complete/suppress) with idempotency; (4) scheduler and callback ingress; (5) PostgreSQL tests including DST and one-logical-offer races.

## Developer handoff

Not implemented in this session. W017 (its M4 dependency) is complete and committed. Product behavior is fixed by D030; the remaining blockers are technical (callbacks, scheduler, scheduled-outbox model), to be recorded as a technical decision before coding.

## QA result and completion

Not run — implementation not started. Definition of done: all acceptance criteria observable through retained tests on local PostgreSQL, with real Telegram callback behavior explicitly scoped or noted as unverified.
