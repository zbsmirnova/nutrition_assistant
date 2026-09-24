# QA strategy and definition of done

Status: working process, established 2026-09-22.
Owner: lead assistant maintains the strategy; QA owns the evidence it produces.

## Inputs and independence

QA reads accepted requirements in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), the relevant specification/decision records, and the work brief's acceptance criteria before relying on an implementation summary. Develop expected outcomes independently and test a reproducible revision. Developer-authored fixtures are useful shared inputs, not proof that the implementation understands messages or persists changes.

The developer provides runnable setup, synthetic seeds, the revision under review, checks already run, and known limitations. The QA report distinguishes its own checks from reported developer results. If no separate QA review ran, describe the evidence as developer verification.

Latest completed review: [004-nebius-adapter-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa.md?type=file&root=%252F). W004 passed all eight criteria after the recorded Retry-After whitespace fix. Injected-response checks verify the adapter/worker boundary; live compatibility, language accuracy, latency and cost still require separate evidence. Earlier W003 failures and its final pass remain preserved in its report.

## Current verification boundary

Current developer suites contain 118 offline contract/arithmetic/protocol/resolver checks, 103 PostgreSQL integration checks, and 32 retained independent checks from M1/W002/W003/W004. W003 developer runs cover controlled single-food resolution, dairy ambiguity, claim races, actual process crashes, and populated upgrade. W013/W014 cover bounded saved-recipe lookup, ambiguity, selection/name answers, and grams resumption; W015 adds the exact-weight/gross-basis guard, W016 adds user-approved-estimate provenance, W022 adds trusted recipe provisioning, and W023 adds durable clarification outbox/rendering coverage. These suites do not establish live model quality. The earlier W001/W002 reports preserve their own reviewed snapshots, findings, root-assisted database execution, and limits. Runtime remains Python 3.14.0 / PostgreSQL 17.11. Controlled parser responses remain expected proposals, not measured live-model behavior. Live Nebius evaluation is recorded separately in [interpretation-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/interpretation-evals-v1.md?type=file&root=%252F); the provider quality, exact-weight, approved-estimate, trusted-provisioning, and clarification-delivery paths have developer coverage only.

From the repository root, after following [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F):

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
~~~

The first command runs offline contracts/arithmetic/protocol/resolver checks; the second and third explicitly exercise local PostgreSQL. Each database test owns a random schema with no fallback to public, then removes only that schema. The independent suite adds database insertion/commit failures, populated migration rollback, conflicting concurrent payloads, and frozen date/version checks. A missing database fails the run. The explicit nebius-smoke command sends a fixed synthetic request without database access; no live run is recorded. General model/Telegram evaluation is not implemented.

Source entry points: [test_contracts.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_contracts.py?type=file&root=%252F), [test_nutrition.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_nutrition.py?type=file&root=%252F), and [test_food_service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/integration/test_food_service.py?type=file&root=%252F). The recorded M1 developer handoff/evidence is [001-persist-food-entry-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-developer.md?type=file&root=%252F).

Independent evidence is in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F), with retained probes in [test_w001_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w001_independent.py?type=file&root=%252F). Its closeout addendum distinguishes the reviewed source from later documentation and evidence packaging.

W002 evidence is in [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F), including its original receipt failure and passing recheck. Additional retained checks are in [test_w002_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w002_independent.py?type=file&root=%252F). The original probe and the separately hashed retention copy are both preserved.

## Coverage by layer

| Layer | Evidence expected | Current state |
| --- | --- | --- |
| Contract | Closed shapes, malformed inputs, candidate scope, source/revision guards, generated-schema drift. | Executable suite exists; not a substitute for stateful checks. |
| Nutrition/domain | Independently calculated scaling and aggregation; units/basis; bounds; unknowns; rounding and overflow boundaries; recipe yield. | Nine product-food arithmetic tests plus database overflow/unknown-value checks. Recipe arithmetic remains authored-fixture coverage only. |
| Persistence/application | Real PostgreSQL constraints and transactions; current pointers; idempotency; concurrent work; fault injection; process restart; ownership. | 103 integration checks cover M1/W002/W003/W004/W011–W016/W022 and the Telegram bot-acknowledgment, saved-recipe correction, and ordinary-food correction confirmation regressions; 32 retained QA checks remain. Independent W003/W004 reviews passed; their reports preserve source-specific attribution. |
| Conversation | Intent distinctions, pending state, mixed messages, target ambiguity, corrections/undo, source dates, dependent actions. | W003 controlled single-food resolution and dairy deferral are executable. Full clarification/mixed/correction flows remain planned. |
| LLM evaluation | Fixed annotated cases, held-out cases, reproducible provider/model/prompt/schema versions, measured intent/argument/clarification errors. | Not run; Nebius Token Factory selected in D009. Exact model, schema compatibility, and thresholds remain unverified. |
| Transport/check-in | Authenticated ingress; outbox recovery; uncertain sends; bounded MVP processing; inline keyboards; stale callbacks; dinner/reminder and date-bound responses. | Private Telegram ingress, sending adapters, and W020's one-owner operator loop exist with synthetic protocol tests and real-database recovery checks. The entire dinner/reminder/check-in/closure runtime is post-MVP W018; no MVP callback or scheduler is implemented. |
| Personal release | End-to-end scenarios, startup/deployment, monitoring redaction, backup/restore, agreed export/deletion and retention behavior. | Not run; M6. |

The original 27 behavioral scenarios are preserved in [scenarios-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/scenarios-v1.md?type=file&root=%252F), with explicit coverage limits. The user-authored food-intake calculation draft is [food-intake-calculation-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/food-intake-calculation-evals-v1.md?type=file&root=%252F), date-resolution draft is [time-resolution-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/time-resolution-evals-v1.md?type=file&root=%252F), and recipe drafts are [recipe-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/recipe-evals-v1.md?type=file&root=%252F) plus [recipe-calculation-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/recipe-calculation-evals-v1.md?type=file&root=%252F). They are inputs to test design, not completed QA reports.

## Required regression families

These are coverage categories, not a duplicate of every test case. Add executable regression cases as the corresponding layer becomes available, using requirement IDs in test names or case metadata where practical.

| Family | Requirements | Cases to preserve |
| --- | --- | --- |
| Intake and correction | FOOD-001–FOOD-005, DATA-002 | Clear item, 100 g → 80 g same entry, additional portion, plan/question non-consumption, undo, duplicate delivery versus a new identical message. |
| Clarification | FOOD-002/FOOD-004 | Save clear soup while bread waits; answer adds only bread; pending correction retains old values; unrelated weight input does not answer a food question; delayed answer retains original date. |
| Nutrition | CALC-001/CALC-002 | Known/partial/unknown nutrients, edible versus gross/bones, raw/cooked and volume/mass compatibility, finite decimal bounds, independently calculated totals. |
| Recipes | RECIPE-001–RECIPE-003 | Original ingredient amounts/instructions retained; per-100-g calculation; required yield; no default portion/batch; saving recipe is not eating; historical source versions stay pinned. |
| Observations | OBS-001/OBS-002 | One daily weight/steps slot; replacement; identical-value no-op; explicit increment once; zero versus missing; conflict/backdating. |
| Completion/check-in | DAY-001–DAY-003 | Post-MVP W018: dinner and scheduled reminder share one logical offer; closure, missing steps, late food, callbacks, DST, and activity reply date are tested together. MVP records food and steps independently and has no close-day command. |
| Isolation/recovery | DATA-001–DATA-003 | Foreign-user references rejected; before/after-commit failure; replayed increments; stale versions; process restart; current-pointer integrity; privacy-safe operational logs. |
| Replies and reports | FOOD-006, CALC-002, UX-001 | Committed entry plus fresh day totals, visible pending/partial coverage, no false zero-intake day, complete-day denominators, nonjudgmental language. |

The existing 20 authored examples are indexed by [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F). Preserve their distinction from a held-out evaluation set: examples used in prompts or implementation tuning must not also be presented as unseen evaluation cases.

## Revision and environment evidence

Record the full commit SHA, runtime/dependency versions, relevant configuration, migration version, seed data, commands, and results. Check the revision and tree state before and after testing so edits during a run are visible.

If testing uncommitted changes, capture the base commit plus a reproducible patch or workspace snapshot that includes untracked relevant files; record an identifier/hash and its location. A bare base SHA is insufficient. Do not commit or upload unrelated work just to create QA evidence. Run from an isolated checkout/worktree when one has been authorized and is available.

Use synthetic records and scoped disposable databases; never run destructive tests against real user data. Test credentials and real message payloads must not appear in a report. Parallel reviewers must not mutate each other's files or databases.

Record each check as passed, failed, blocked, or not run. A blocked dependency is not a pass. Keep reproduction steps, expected/actual behavior, and evidence for failures. Associate rechecks with the new revision; prior results remain evidence only for their recorded revision.

## Completion and release criteria

A work brief is done when its agreed scope is implemented, acceptance criteria have appropriate evidence, relevant regressions pass, blocking defects are resolved, documentation is current, and a reproducible QA result is linked. For implementation slices, require independent review as planned; do not silently relabel self-review as independent QA.

Treat data loss, duplicate or unauthorized mutations, incorrect totals presented as complete, and broken core acceptance criteria as blockers. Record lesser defects with impact and disposition. If a scope reduction is authorized, update the decision and criteria explicitly.

Passing one slice is not a release verdict. M6 additionally requires agreed real-data/privacy/hosting decisions, end-to-end behavior, and operational evidence. No current contract result establishes personal-release readiness.

## Documentation checks

For documentation-only changes, inspect local link targets, proposed/accepted/implemented labels, requirement consistency, ownership of status, and runnable commands. Check formatting and avoid empty reports implying QA occurred. A document edit does not require new behavioral tests when no behavior changed.
