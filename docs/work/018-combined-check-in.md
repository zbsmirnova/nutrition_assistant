# W018 — Combined completion/activity check-in

Status: ready.
Milestone: M5 (depends on M4 observations, done in W017).
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D030 and D031 (dinner-triggered behavior and MVP scope), under DAY-001 and D001; callback mechanics remain technical work.

## Outcome and scope

Offer a single combined completion/activity check-in with the dinner acknowledgment and act on the user's choice. By D030 and D031, there is no scheduled fallback or automatic reminder when dinner is absent. The buttons are "Everything logged", "Add steps", and "Later"; "Later" dismisses; "Add steps" asks for steps in-flow and records a daily-steps observation via W017; and the completion action is suppressed after conversational closure or explicit completion. Late food after closure never creates a second logical offer.

## Requirements and decisions

DAY-001; D001 (optional completion); D030/D031 (dinner-triggered behavior and MVP scope); section 9 of the data model (`daily_check_ins` and ordinary outbox). W017/D029 provide the steps observation the "Add steps" path reuses.

Dependencies that are technical decisions for this slice (not yet built):

- Telegram transport must gain inline-keyboard sends and `callback_query` ingress with `answerCallbackQuery`; the current transport only sends plain text and ignores non-text updates.
- Dinner-triggered offers need one durable daily-check-in identity and must be idempotent across worker retries and concurrent dinner messages.

These mechanics are unresolved technical design and should be recorded in a follow-up technical decision before implementation; the user-facing behavior and MVP scope are settled by D030/D031.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W018-A01 | A recognized dinner produces one outgoing message combining the acknowledgment and the check-in offer with the three actions. |
| W018-A02 | With no dinner, no automatic check-in or scheduled reminder is created in MVP. |
| W018-A03 | "Everything logged" marks the day complete; "Add steps" records the day's steps as an observation; "Later" dismisses without reschedule. |
| W018-A04 | One dinner-triggered logical offer per local day across retries and races; later dinner messages do not create a second offer. |
| W018-A05 | After closure or completion the completion action is suppressed; late food additions keep the day complete with no new check-in. |
| W018-A06 | Old or superseded callbacks validate current state and their bound local date; ambiguous sends are visible and not blindly duplicated. |

## Implementation checklist

Not started. Ordering proposal: (1) technical decision for callback transport and dinner-offer persistence; (2) migration for `daily_check_ins` and callback/action state; (3) offer lifecycle service (attach/dismiss/complete/suppress) with idempotency; (4) callback ingress and inline-keyboard delivery; (5) PostgreSQL tests for stale callbacks, retries, and one-logical-offer races. Scheduled reminders, scheduler, DST, and scheduled-outbox delivery are deferred by D031 to [W019](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/019-scheduled-check-in-reminders.md?type=file&root=%252F).

## Developer handoff

Not implemented in this session. W017 (its M4 dependency) is complete and committed. Product behavior and MVP scope are fixed by D030/D031; the remaining blocker is the technical design for callbacks and dinner-offer persistence before coding.

## QA result and completion

Not run — implementation not started. Definition of done: all acceptance criteria observable through retained tests on local PostgreSQL, with real Telegram callback behavior explicitly scoped or noted as unverified.
