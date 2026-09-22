# Delivery roadmap

Updated: 2026-09-22. Owner: lead assistant.
This file owns milestone status and order. Individual task status and acceptance criteria belong in their work briefs.

## Current position

M1 now has a local PostgreSQL application path for a resolved product-food command, with frozen operation identity, deterministic totals, atomic revisions/results/outbox, and fake delivery. Developer checks pass: 32 contract tests, 9 arithmetic tests, and 26 PostgreSQL integration tests on Python 3.14.0 / PostgreSQL 17.11. The original three schemas and 20 authored parser scenarios are unchanged.

The current brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F). Independent QA has passed; M1 is complete for its local persistence scope. Telegram and live interpretation belong to M2, not to the current verification claim.

## Milestones

| ID | Milestone / status | Depends on | Exit criteria |
| --- | --- | --- | --- |
| M0 | Contracts and development foundation — complete for its stated scope | — | Product baseline, logical model, conversation rules, typed boundaries, authored examples, contract checks, document ownership, decision register, and first work brief exist. This is not approval of every proposed technical detail or independent QA of the application. |
| M1 | Durable food command — complete | M0 | Fresh local PostgreSQL setup; seeded owned product data; resolved add-food command; deterministic entry/day totals; atomic mutation/result/response intent; retries, restart recovery, and cross-user rejection verified. |
| M2 | Conversational food and corrections — planned | M1 | Telegram ingress/identity and delivery; provider adapter; scoped reference resolution; Russian intent evaluation; pending clarifications; same-entry correction/delete/undo; independent clear items saved once; entry-plus-day replies. |
| M3 | Recipes — planned | M1; M2 for conversation | Save original ingredient amounts/instructions and versioned per-100-g nutrition; clarify material inputs; deterministic calculations; log eaten grams; keep historical meals pinned to prior versions. |
| M4 | Daily observations and completion — planned | M2 | One revisable daily weight and steps total; explicit increments; backdating; shared completion command; missing steps do not block completion; late additions preserve completeness; history shows coverage. |
| M5 | Combined check-in and reports — planned | M3, M4 | Dinner/21:00 flow; closure suppresses completion action; one logical daily offer across retries/races; date-bound replies and DST checks; daily/weekly reporting coverage; agreed schedule and outage behavior. |
| M6 | Personal release readiness — planned | M1–M5; deployment decisions | Agreed hosting/privacy/provider/retention/export/deletion behavior; reproducible deployment; monitoring; restore rehearsal; end-to-end acceptance and remaining-risk review. |

V1 requires food, weight, steps, recipes, and the accepted check-in. Release-readiness details still need decisions; listing them here does not imply that unanswered product choices have been approved. Weekly-report scheduling is open.

Milestone statuses: planned, in progress, complete, blocked. The first implementation task's preparation and QA states are tracked in its brief, not duplicated here.

## Implementation sequence now

1. Plan M2's authenticated Telegram ingress and delivery using the working persistence boundary.
2. Resolve provider/data-use choices needed for interpretation.
3. Implement scoped resolution, clarification, and corrections through bounded M2 slices.

Use [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F) for unresolved questions and blockers. Use [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F) for verification expectations.

## Later scope

- V2: training sessions and sets.
- Prioritize separately: additional activity/measurements, menstrual-cycle context, Apple Health integration, habitual shortcuts, external catalogs/barcodes, historical import, and broader user access.
- Before multi-user release, review access isolation, deletion behavior, and PostgreSQL row-level security with a runtime role that cannot bypass it.

## Completion evidence

| Milestone | Evidence | Limits |
| --- | --- | --- |
| M0 | [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F), [test_contracts.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_contracts.py?type=file&root=%252F), existing specifications, and the maintained document set. Contract suite: 32 passed on 2026-09-22. | Developer verification; no separate QA verdict, live-model measurement, database integration, or deployed service. |
| M1 | Local migrations, seeded command demo, 9 arithmetic checks and 26 real PostgreSQL checks; developer evidence in [001-persist-food-entry-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-developer.md?type=file&root=%252F). | Implementation and independent QA complete for the local persistence scope. Fake delivery only; no live parsing or Telegram. |

Detailed QA evidence for later slices belongs in reports linked from their work briefs.
