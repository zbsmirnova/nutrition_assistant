# W023 — Durable Telegram clarification delivery

Status: done.  
Milestone: M2 MVP pilot.  
Owner: lead assistant, architect/developer.  
Decision: D038, building on D026, D027, W006, W014, and W020.

## Outcome and scope

Pending exact-weight, dairy-fat, and saved-recipe ambiguity questions now use
the durable Telegram outbox. The worker records pending state and a typed
`needs_clarification` response atomically; the existing sender renders the
question and replies to the original user message. Scheduled reminders,
inline callbacks, close-day behavior, and a nutrition source for unknown
restaurant food remain outside this slice.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W023-A01 | A supported unresolved clarification stores no food mutation and queues one typed question in the same transaction. |
| W023-A02 | The queued question uses the original Telegram source for reply association and remains retryable through the existing outbox worker. |
| W023-A03 | Replaying the worker or delivery path does not create a duplicate question or food entry. |
| W023-A04 | Dairy-fat, quantity, and recipe ambiguity prompts retain their typed question kind and bounded candidate choices. |
| W023-A05 | Existing clarification answers still resume the frozen operation once, with pending food excluded until resolution. |

## Implementation and verification

- [x] Persist an idempotent clarification notification without a migration.
- [x] Render `needs_clarification` outcomes through the Telegram sender.
- [x] Cover unknown dairy fat, recipe ambiguity, and rendering behavior.
- [x] Keep model interpretation separate from notification delivery and writes.

Developer verification on the completion revision:

- offline suite: 118 tests;
- PostgreSQL integration suite: 103 tests;
- retained QA suite: 32 checks;
- `git diff --check`: passed.

User-run live pilot on 2026-09-24: the bot asked for missing grams for the
saved recipe `Овсяная каша`; a reply of `200 г` to the original source resumed
the frozen operation and returned `status: applied` / `delivery: sent`, with
152 kcal recorded. Existing pending items remained outside the day total.
This is one end-to-end example, not broad model-quality evidence. No
independent QA review was run.
