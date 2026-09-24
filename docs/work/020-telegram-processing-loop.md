# W020 — Bounded Telegram MVP processing loop

Status: done.
Milestone: M2 (MVP pilot tooling; does not add post-MVP scheduling).
Owner: lead assistant, architect/developer.
Updated: 2026-09-24.
Decision: D034, using W002 transport, W003 worker, W004 Nebius adapter, and D033 backend-derived evidence.

## Outcome and scope

Add one explicit `telegram-process` command that polls one bounded batch, processes the next eligible message for one supplied owner through Nebius, and dispatches one queued response. Keep polling, interpretation, durable job claims, retries, and outbox delivery as their existing separate components. When the source message is available, the Telegram response is sent as a reply to that message so delayed processing remains attributable. Do not add a daemon, scheduler, callback keyboard, close-day command, or multi-user dispatcher.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W020-A01 | The command requires an owner UUID, validates the bot configuration, polls with the requested bounded timeout, and does not print credentials or source text. |
| W020-A02 | It invokes the existing worker without an explicit source so the worker selects the owner's oldest eligible job and preserves durable claim/retry behavior. |
| W020-A03 | It dispatches one queued response through the existing Telegram sender and reports only poll, processing, and delivery status. |
| W020-A04 | Existing commands and the separate synthetic/fake paths remain unchanged. |
| W020-A05 | Focused CLI/protocol tests and the complete offline suite pass; no live Telegram or model result is claimed. |

## Implementation and verification

- [x] Add the `telegram-process` CLI composition.
- [x] Keep output redacted to operational status fields.
- [x] Add the D034 decision and README operator instructions.
- [x] Run focused Nebius/CLI tests and the complete offline suite.
- [x] Preserve source-message association on Telegram acknowledgments through `reply_parameters`.

Developer verification: focused Nebius/CLI tests passed, followed by 117 offline tests, 103 PostgreSQL integration tests, and 32 retained QA tests on 2026-09-24. A user-run pilot verified bot identity and private-message ingestion (`accepted: 1`). After the runtime prompt was strengthened with an explicit undated-source null-date example, the live smoke passed; a message without a matching catalog item was held as `product_unresolved` with no food mutation. After W021 provisioned a known product, a later message completed with `status: applied` and `delivery: sent`. The bounded worker now also resolves W017 weight and steps proposals into trusted observation commands; the user confirmed live set-plus-increment steps processing after the queued messages were drained. Source-linked Telegram replies are verified by unit and PostgreSQL transport tests; the pilot also demonstrated why one-message-per-run acknowledgments need that source association. Follow-up tests map replies to the bot's sent acknowledgment through the outbox operation back to the same food entry, recover an unmatched provider description fragment using that backend reply target, correct a saved recipe by changing its eaten grams in the same entry, and render correction acknowledgments for both recipe and ordinary product entries. A natural correction therefore does not require replying to the original user message. The bot response reported one older pending action from the unmatched message; clarification delivery for that branch remains outside this slice. No independent QA review was run.

## Deferred acknowledgment copy improvements

Product-owner notes for a later rendering slice; no implementation change is made here:

- Use `Итого за сегодня:` in the normal current-day acknowledgment instead of the dated phrase.
- Continue persisting all nutrients, but hide fat and carbohydrate lines from the Telegram acknowledgment.
- Remove the pending-clarification count from the normal acknowledgment.
- Remove the day-completeness sentence from routine food acknowledgments.

These are presentation-only changes. Nutrition persistence, daily totals, pending-state accounting, and the no-close-day MVP rule remain unchanged until the rendering behavior is explicitly implemented and tested.

## Usage

~~~sh
.venv/bin/python -m nutrition_app telegram-process --user INTERNAL_USER_UUID --timeout 25
~~~

Repeat the command to process another message or retry a durable job. Use the separate commands when diagnosing a specific source or delivery state.
