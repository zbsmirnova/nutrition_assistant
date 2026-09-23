# Delivery roadmap

Updated: 2026-09-23. Owner: lead assistant.
This file owns milestone status and order. Individual task status and acceptance criteria belong in their work briefs.

## Current position

M1 is complete: a local PostgreSQL application path for a resolved product-food command, with frozen operation identity, deterministic totals, atomic revisions/results/outbox, and fake delivery. Verification passes: 32 contract tests, 9 arithmetic tests, 26 PostgreSQL integration tests, and 10 independently authored QA probes on Python 3.14.0 / PostgreSQL 17.11. The original three schemas and 20 authored parser scenarios are unchanged.

The completed brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F). M2 remains in progress. W002 private Telegram transport is complete and independently reviewed with synthetic API responses. The latest completed slice is [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F): durable single-food interpretation/resolution with controlled responses and dairy ambiguity handling. It passed independent review after its recorded resolver fixes; the brief owns the exact evidence. The completed [004-nebius-adapter.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F) adds the explicit Nebius adapter, with all eight criteria independently reviewed using simulated responses. Live interpretation and real-bot operation remain unverified.

## Milestones

| ID | Milestone / status | Depends on | Exit criteria |
| --- | --- | --- | --- |
| M0 | Contracts and development foundation — complete for its stated scope | — | Product baseline, logical model, conversation rules, typed boundaries, authored examples, contract checks, document ownership, decision register, and first work brief exist. This is not approval of every proposed technical detail or independent QA of the application. |
| M1 | Durable food command — complete | M0 | Fresh local PostgreSQL setup; seeded owned product data; resolved add-food command; deterministic entry/day totals; atomic mutation/result/response intent; retries, restart recovery, and cross-user rejection verified. |
| M2 | Conversational food and corrections — in progress | M1 | Telegram ingress/identity and delivery; provider adapter; scoped reference resolution; Russian intent evaluation; pending clarifications; same-entry correction/delete/undo; independent clear items saved once; entry-plus-day replies. |
| M3 | Recipes — in progress (W011 persistence) | M1; M2 for conversation | Save original ingredient amounts/instructions and versioned per-100-g nutrition; clarify material inputs; deterministic calculations; log eaten grams; keep historical meals pinned to prior versions. |
| M4 | Daily observations and completion — planned | M2 | One revisable daily weight and steps total; explicit increments; backdating; shared completion command; missing steps do not block completion; late additions preserve completeness; history shows coverage. |
| M5 | Combined check-in and reports — planned | M3, M4 | Dinner/21:00 flow; closure suppresses completion action; one logical daily offer across retries/races; date-bound replies and DST checks; daily/weekly reporting coverage; agreed schedule and outage behavior. |
| M6 | Personal release readiness — planned | M1–M5; deployment decisions | Agreed hosting/privacy/provider/retention/export/deletion behavior; reproducible deployment; monitoring; restore rehearsal; end-to-end acceptance and remaining-risk review. |

V1 requires food, weight, steps, recipes, and the accepted check-in. Release-readiness details still need decisions; listing them here does not imply that unanswered product choices have been approved. Weekly-report scheduling is open.

Milestone statuses: planned, in progress, complete, blocked. The first implementation task's preparation and QA states are tracked in its brief, not duplicated here.

## Implementation sequence now

1. Independently review the completed W010 numbered ambiguous-target selection and date/meal correction slice, then proceed to recipe persistence/consumption. W006's reply-linked dairy clarification, W007's one-clear-plus-one-pending path, W008's trusted correction/delete/restore execution, W009's bounded conversational entry targets, and W010's bounded selection/fields are complete only for their bounded synthetic scopes; W003's worker still does not replace the remaining accepted requirements.
2. Configure and smoke-check the selected Nebius model through W004’s explicit synthetic command, then measure Russian interpretation quality. The user supplies NEBIUS_API_KEY as a secret; keep NUTRITION_LLM_MODEL configurable and select it through measured Russian-language evaluation. Q09’s remaining request/evaluation choices and Q10’s data-lifecycle choices stay in the question register. Offline adapter verification is complete. The user has configured a key and candidate model and reported a live completion that passed schema/reference checks; resolving the synthetic smoke expectation and measuring interpretation quality remain next. The W004 brief owns the exact setup evidence.
3. Complete W012 recipe consumption, then add conversational recipe lookup/resolution on top of completed W005/W011 foundations while preserving M2 clarification/resumption and corrections. Runtime comparison with a general food database is deferred by D020; W005's USDA comparison remains offline evaluation only. W003's bounded worker does not replace these accepted requirements.

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

W003 worker evidence is in [003-conversation-worker-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/003-conversation-worker-qa.md?type=file&root=%252F). All eleven criteria passed for the frozen synthetic source. W004 adapter evidence is in [004-nebius-adapter-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa.md?type=file&root=%252F). All eight criteria passed with simulated responses and PostgreSQL recovery checks; actual model/schema compatibility remains unverified. Detailed evidence for later slices belongs in reports linked from their work briefs.
