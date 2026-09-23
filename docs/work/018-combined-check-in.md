# W018 — Combined dinner/activity check-in and reminders

Status: planned (post-MVP).
Milestone: M5 (post-MVP; depends on M4 observations, completed in W017).
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D032 supersedes the earlier MVP check-in scope in D030/D031; DAY-001–DAY-003 remain future requirements.

## Outcome and scope

Add one optional post-MVP daily interaction that can be triggered by a recognized dinner message or by an enabled local-time reminder. The two triggers share one durable daily-check-in identity and one suppression/closure state. The interaction may acknowledge dinner, ask for steps, and offer a user-controlled completion action. The exact closure semantics are part of this slice; MVP has no close-day command, completion button, dinner trigger, scheduled reminder, or callback transport.

Food remains continuously persisted as each accepted operation arrives. Steps remain an independent daily observation through W017. A late food message updates food totals and does not create a second check-in. Unknown restaurant nutrition remains pending until the user supplies an approved portion and a separately defined nutrition source.

## Requirements and decisions

D032; DAY-001–DAY-003; D001 for optional completion; W017/D029 for the daily steps observation. W019 is merged into this brief: dinner-triggered and scheduled reminder behavior must be designed and implemented together so they cannot diverge in identity, suppression, or callback handling.

Technical decisions required before implementation:

- Telegram delivery needs inline-keyboard sends, callback-query ingress, server-side opaque action binding, and stale/foreign callback validation.
- Dinner and reminder triggers need one idempotent `(user, local date)` check-in identity. Whichever trigger commits first suppresses the other.
- The scheduler needs a database-backed occurrence key, IANA time-zone conversion, explicit DST behavior, outage/missed-occurrence policy, and a durable delivery path. PostgreSQL advisory locking and a scheduled outbox are proposals, not accepted decisions.
- Closure must be a domain state separate from food persistence. The implementation must define whether and how a future completion action affects reports, missing steps, pending food, and later edits.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W018-A01 | An enabled dinner trigger or scheduled reminder creates at most one post-MVP check-in for a user's local date. |
| W018-A02 | The two trigger paths share one durable identity and suppress duplicate offers across retries, races, late dinner, and process restarts. |
| W018-A03 | The interaction can acknowledge the current log, request or record the day's steps, and apply the accepted closure behavior without changing food-entry persistence. |
| W018-A04 | A late food addition updates totals and does not create another check-in; pending/unknown food remains visible and outside totals. |
| W018-A05 | Callback actions are bound to user, local date, check-in state, and action version; stale, foreign, duplicate, and uncertain callbacks are safe. |
| W018-A06 | Scheduler occurrence, DST, outage, retry, and uncertain-send behavior is covered by retained tests and documented operationally. |

## Implementation checklist

Not started. First record the combined callback/scheduler/outbox technical decision. Then implement the shared check-in/closure state, callback transport, scheduler occurrence planner, durable delivery integration, and PostgreSQL/Telegram protocol tests. Do not start W018 by adding a close-day command to the MVP worker.

## Developer handoff

W017 provides the independent daily steps write path. No W018 runtime is implemented. The previous W019 brief is retained as a historical proposal and is merged into this work item.

## QA result and completion

Not run — implementation not started. Definition of done: all acceptance criteria are observable through retained tests, with live Telegram delivery and scheduler operations explicitly verified or recorded as unverified.
