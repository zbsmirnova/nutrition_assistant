# Delivery roadmap

Updated: 2026-09-22. Owner: lead assistant.
This file owns milestone status and order. Individual task status and acceptance criteria belong in their work briefs.

## Current position

M1 is complete: a local PostgreSQL application path for a resolved product-food command, with frozen operation identity, deterministic totals, atomic revisions/results/outbox, and fake delivery. Verification passes: 32 contract tests, 9 arithmetic tests, 26 PostgreSQL integration tests, and 10 independently authored QA probes on Python 3.14.0 / PostgreSQL 17.11. The original three schemas and 20 authored parser scenarios are unchanged.

The completed brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F). Independent QA passed the local scope with root-assisted database execution; documentation observations were resolved. M2 is now in progress through [002-telegram-transport.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/002-telegram-transport.md?type=file&root=%252F). W002 private Telegram transport is complete and independently reviewed with synthetic API responses. The current suites contain 106 checks with passing evidence; the report records targeted rechecks and inherited unchanged-code results. Live interpretation and real-bot operation remain unverified.

## Milestones

| ID | Milestone / status | Depends on | Exit criteria |
| --- | --- | --- | --- |
| M0 | Contracts and development foundation — complete for its stated scope | — | Product baseline, logical model, conversation rules, typed boundaries, authored examples, contract checks, document ownership, decision register, and first work brief exist. This is not approval of every proposed technical detail or independent QA of the application. |
| M1 | Durable food command — complete | M0 | Fresh local PostgreSQL setup; seeded owned product data; resolved add-food command; deterministic entry/day totals; atomic mutation/result/response intent; retries, restart recovery, and cross-user rejection verified. |
| M2 | Conversational food and corrections — in progress | M1 | Telegram ingress/identity and delivery; provider adapter; scoped reference resolution; Russian intent evaluation; pending clarifications; same-entry correction/delete/undo; independent clear items saved once; entry-plus-day replies. |
| M3 | Recipes — planned | M1; M2 for conversation | Save original ingredient amounts/instructions and versioned per-100-g nutrition; clarify material inputs; deterministic calculations; log eaten grams; keep historical meals pinned to prior versions. |
| M4 | Daily observations and completion — planned | M2 | One revisable daily weight and steps total; explicit increments; backdating; shared completion command; missing steps do not block completion; late additions preserve completeness; history shows coverage. |
| M5 | Combined check-in and reports — planned | M3, M4 | Dinner/21:00 flow; closure suppresses completion action; one logical daily offer across retries/races; date-bound replies and DST checks; daily/weekly reporting coverage; agreed schedule and outage behavior. |
| M6 | Personal release readiness — planned | M1–M5; deployment decisions | Agreed hosting/privacy/provider/retention/export/deletion behavior; reproducible deployment; monitoring; restore rehearsal; end-to-end acceptance and remaining-risk review. |

V1 requires food, weight, steps, recipes, and the accepted check-in. Release-readiness details still need decisions; listing them here does not imply that unanswered product choices have been approved. Weekly-report scheduling is open.

Milestone statuses: planned, in progress, complete, blocked. The first implementation task's preparation and QA states are tracked in its brief, not duplicated here.

## Implementation sequence now

1. Resolve Q09/Q10 sufficiently for the parser adapter: provider/local-model preference and permitted message context. A preference was requested; until answered, verification remains synthetic.
2. Define and implement the conversation-worker slice, including durable inbox resumption, scoped product resolution, and explicit food-message evaluation cases.
3. Extend to clarification, mixed messages, and same-entry corrections through subsequent M2 tasks.

Use [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F) for unresolved questions and blockers. Use [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F) for verification expectations.

## Later scope

- V2: training sessions and sets.
- Prioritize separately: additional activity/measurements, menstrual-cycle context, Apple Health integration, habitual shortcuts, external catalogs/barcodes, historical import, and broader user access.
- Before multi-user release, review access isolation, deletion behavior, and PostgreSQL row-level security with a runtime role that cannot bypass it.

## Completion evidence

| Milestone | Evidence | Limits |
| --- | --- | --- |
| M0 | [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F), [test_contracts.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_contracts.py?type=file&root=%252F), existing specifications, and the maintained document set. Contract suite: 32 passed on 2026-09-22. | Developer verification; no separate QA verdict, live-model measurement, database integration, or deployed service. |
| M1 | Local migrations, seeded demo, 9 arithmetic checks, 26 integration checks, and 10 independent probes; [001-persist-food-entry-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-developer.md?type=file&root=%252F) and independent pass in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F). | Local persistence scope passed; QA database execution was root-assisted. Fake delivery only; no live parsing or Telegram. |

M2 transport evidence is in [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F); all eight W002 criteria passed after the receipt fix. The parser and conversational workflows remain necessary to complete M2.

Detailed QA evidence for later slices belongs in reports linked from their work briefs.
