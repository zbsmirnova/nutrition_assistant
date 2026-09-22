# W001 — Persist one food entry with correct totals and safe retries

Status: done.
Milestone: M1.
Owner: lead assistant, acting as architect/developer; independent QA reviewer: independent_m1_qa.
Updated: 2026-09-22.

Implementation, developer verification, independent QA, and documentation closeout are complete. D002/D003/D006 record the delegated technical choices; product behavior has not been expanded beyond the slice.

## Outcome

Given an authenticated internal user and an already resolved add-food command referring to an owned, seeded product version, save one food entry, return its nutrition and current day totals, and preserve the result across retries and process restarts.

Use synthetic data in local PostgreSQL. This is the first persistence/application slice, not yet a conversational Telegram release.

## Scope and boundaries

Include only the identity, inbox/source evidence, stable operation records, versioned seeded product/source, food-day/entry/revision/component, and response-intent data needed for this flow. Implement deterministic calculation and current-day querying, operation retry handling, ownership validation, and a fake delivery adapter sufficient to exercise recovery.

Seed data and the test harness may supply the catalog/reference context. Do not implement recipe CRUD, live LLM interpretation, pending conversation flows, correction/delete UI, observations, scheduler, production transport, deployment, or historical migration in this slice. Design stable entry/revision storage so later corrections fit without changing identity.

## Requirements and decisions

- FOOD-001, FOOD-006, RECIPE-003, CALC-001/CALC-002, DATA-001–DATA-003 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F).
- [0002-command-execution.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0002-command-execution.md?type=file&root=%252F) and [0003-relational-storage.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0003-relational-storage.md?type=file&root=%252F) are accepted M1 technical decisions; D006 defines the numeric policy.
- [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F) supplies the logical model; implement only the required subset.
- Reuse [commands.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_contracts/commands.py?type=file&root=%252F) and [results.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_contracts/results.py?type=file&root=%252F); generated shapes alone do not implement their semantics.
- Q01–Q03 are resolved for M1 in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). Hosting, real-data retention, and provider selection do not block this synthetic local slice.

## Acceptance criteria

| ID | Observable result and verification |
| --- | --- |
| W001-A01 | Documented setup creates an isolated test PostgreSQL database from migrations. A fresh database and a database already at the current migration both start successfully. Tests do not depend on a developer's existing rows. |
| W001-A02 | Seed product A for user A at 100 kcal, 4 g protein, 4 g fat, 12 g carbohydrate per 100 g. Applying 250 g creates one entry/current revision and returns 250 kcal, 10 g protein, 10 g fat, 30 g carbohydrate. Querying that day returns the same totals. These are synthetic test values. |
| W001-A03 | Replaying the same source delivery/operation, including two concurrent attempts, yields one logical food mutation and one durable response intent. A fresh operation from a distinct identical-text message creates a second entry; totals then double. |
| W001-A04 | Inject failure before the mutation transaction commits: no entry, applied operation, or response intent from that transaction survives. An already committed inbox record may survive. Retry applies the command once. |
| W001-A05 | Inject failure after commit and before reply delivery, restart the processing/sender process while keeping the database, and retry. The saved entry/result is recovered, the response intent remains deliverable, and no second portion is added. Do not assert exactly-once external visible messages. |
| W001-A06 | User B cannot read user A's day/entry or mutate using A's product, source, entry, or operation reference. Rejected attempts change no domain data and reveal no private result. Include application checks and applicable database ownership constraints. |
| W001-A07 | A second product has unknown fat. Its consumed fat stays unknown; a day containing both known and unknown fat reports the known subtotal as partial. A wholly unknown nutrient is not displayed as zero; an empty day is not presented as confirmed zero intake. |
| W001-A08 | Stored food retains the selected product/source version, quantity, calculation policy/version, and nutrition snapshot. Changing the product's current version does not change the prior meal or its queried totals. |
| W001-A09 | Returned success and food/day values correspond to committed data. Mutation failures produce no success response intent. Reusing an operation key with an incompatible payload fails without changing its original result. |
| W001-A10 | Concurrent different valid additions for the same user/date are both retained, or a stale request receives an explicit retriable conflict and is resolved once. There is no lost update or silently stale overwrite; a final day query includes both operations. |
| W001-A11 | The effective local date and source/time-zone evidence in the resolved command survive delayed execution and restart. Processing at midnight does not move an existing resolved command to a different day. |
| W001-A12 | Existing contract checks remain green; setup and integration commands, technical decisions, affected specifications, and the QA handoff are updated. |

## Implementation checklist

- [x] Finalize D002/D003 and record the concrete concurrency mechanism and decision authority.
- [x] Resolve local dependencies/database version and rounding/overflow policy; update the register and setup documentation.
- [x] Add reproducible local PostgreSQL setup and minimal migrations with ownership/uniqueness constraints.
- [x] Add synthetic catalog/source seeds and deterministic calculation/current-day querying.
- [x] Implement resolved add-food execution, stable operation deduplication, and atomic response intent.
- [x] Add process-restart/failure/concurrency/ownership integration checks tied to the criteria above.
- [x] Run existing contract checks and appropriate new checks; record results and known limitations.
- [x] Provide a reproducible revision and handoff for independent QA.
- [x] Resolve blocking defects, recheck affected behavior, and update milestone evidence.

## Developer handoff

The implementation supports already resolved product-food additions; no model or Telegram credentials are needed. Start the pinned Compose database, install runtime dependencies, apply migrations, and run the synthetic demo using [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F). Then run both the contract/arithmetic and explicit integration commands.

Developer evidence, exact source snapshot identity, runtime versions, command results, and acceptance mapping are in [001-persist-food-entry-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-developer.md?type=file&root=%252F). The snapshot includes previously uncommitted contract dependencies and the new application files; no commit was created or user staging changed to manufacture a revision.

Known boundaries: trusted local actor interface; product components only; one frozen command per message; no real Telegram, live parser, pending/correction/recipe/observation workflows, RLS, or production deployment. Uncertain sends are retained for later explicit recovery, not automatically repeated. These match the slice's stated scope.

## QA result and completion

Independent QA passed W001/M1: 41 contract/arithmetic checks, 26 existing database checks, and 10 independently authored probes. The QA agent reviewed requirements/source and ran the first suite; the lead executed database suites at QA's request, and QA assessed their raw outputs. Execution attribution, the frozen source identity, acceptance coverage, and limits are recorded in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F).

No blocking implementation findings remained. W001-QA-D01 and W001-QA-D02 were corrected as documentation-only changes. The independent probes are retained in [test_w001_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w001_independent.py?type=file&root=%252F); the repository command passed all 10 after packaging. Closeout changes affect documentation/evidence and add this unchanged probe file; the production implementation remains identical to the reviewed snapshot.

Done requires all applicable acceptance criteria verified, unresolved blocking defects cleared, a reproducible independent QA report linked here, and affected documents updated. Scope changes require an explicit decision and revised criteria, not silently marking a failing criterion inapplicable.
