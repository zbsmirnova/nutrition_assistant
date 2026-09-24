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

Developer verification: focused Nebius/CLI tests passed, followed by 118 offline tests, 103 PostgreSQL integration tests, and 32 retained QA tests on 2026-09-24. A user-run pilot verified bot identity and private-message ingestion (`accepted: 1`). After the runtime prompt was strengthened with an explicit undated-source null-date example, the live smoke passed; a message without a matching catalog item was held as `product_unresolved` with no food mutation. After W021 provisioned a known product, a later message completed with `status: applied` and `delivery: sent`. The bounded worker now also resolves W017 weight and steps proposals into trusted observation commands; the user confirmed live set-plus-increment steps processing after the queued messages were drained. Source-linked Telegram replies are verified by unit and PostgreSQL transport tests; the pilot also demonstrated why one-message-per-run acknowledgments need that source association. Follow-up tests map replies to the bot's sent acknowledgment through the outbox operation back to the same food entry, recover an unmatched provider description fragment using that backend reply target, correct a saved recipe by changing its eaten grams in the same entry, and render correction acknowledgments for both recipe and ordinary product entries. W023 now persists supported clarification questions through the same outbox path and covers their rendering/replay behavior in developer tests. On 2026-09-24 the user completed both an ordinary-product correction pilot and a saved-recipe weight-clarification pilot; Telegram returned the expected correction and then recorded 200 g of `Овсяная каша` at 152 kcal. The MVP acknowledgment follow-up is covered by D042 and [018-mvp-acknowledgment-rendering-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/018-mvp-acknowledgment-rendering-developer.md?type=file&root=%252F); it changes only Telegram wording and visibility, not persistence or totals. A natural correction therefore does not require replying to the original user message, while the clarification answer currently replies to the original source. Unknown catalog/restaurant nutrition still has no automatic source. No independent QA review was run.

## MVP acknowledgment copy

The Telegram renderer now uses the product owner's MVP wording decision:

- Food confirmations use `Итого за сегодня:` and show kcal/protein for the
  entry and updated day total.
- Fat and carbohydrate values remain persisted and calculated but are omitted
  from routine Telegram copy.
- Pending-clarification counts and day-completeness sentences are omitted from
  routine food confirmations. Pending actions remain outside totals according
  to the existing backend rules.
- Weight confirmations use `Вес за сегодня записан: 76,3 кг.`. Steps retain
  their dated confirmation wording for now.

This is presentation-only behavior. Nutrition persistence, daily totals,
pending-state accounting, and the no-close-day MVP rule are unchanged.

## Usage

~~~sh
.venv/bin/python -m nutrition_app telegram-process --user INTERNAL_USER_UUID --timeout 25
~~~

Repeat the command to process another message or retry a durable job. Use the separate commands when diagnosing a specific source or delivery state.
