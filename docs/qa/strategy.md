# QA strategy and definition of done

Status: working process, established 2026-09-22.
Owner: lead assistant maintains the strategy; QA owns the evidence it produces.

## Inputs and independence

QA reads accepted requirements in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), the relevant specification/decision records, and the work brief's acceptance criteria before relying on an implementation summary. Develop expected outcomes independently and test a reproducible revision. Developer-authored fixtures are useful shared inputs, not proof that the implementation understands messages or persists changes.

The developer provides runnable setup, synthetic seeds, the revision under review, checks already run, and known limitations. The QA report distinguishes its own checks from reported developer results. If no separate QA review ran, describe the evidence as developer verification.

Next review target: [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F), once implemented and handed off. Its controlled parser responses will verify the worker/resolver boundary, not live interpretation accuracy. W002 remains the latest completed independent review. Use [TEMPLATE.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/TEMPLATE.md?type=file&root=%252F) for real executions; template placeholders are not results.

## Current verification boundary

Current developer suites contain 32 contract tests, 9 arithmetic tests, 11 protocol/rendering checks, 38 real PostgreSQL integration tests, and 16 retained independent checks from M1/W002. Independent W002 review passed after a receipt-validation fix and targeted rechecks. Database executions were root-assisted and assessed by QA. Runtime remains Python 3.14.0 / PostgreSQL 17.11. Independent M1 QA passed after source/requirement review, rerunning those checks, and adding 10 separate probes. The QA agent ran contract/arithmetic checks; database execution was root-assisted and its raw outputs assessed by QA. The separate report preserves that attribution. Authored parser fixtures remain expected outputs, not measured live-model behavior.

From the repository root, after following [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F):

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
~~~

The first command runs contracts/arithmetic; the second and third explicitly exercise local PostgreSQL. Each database test owns a random schema with no fallback to public, then removes only that schema. The independent suite adds database insertion/commit failures, populated migration rollback, conflicting concurrent payloads, and frozen date/version checks. A missing database fails the run. No live-model or Telegram evaluation command exists yet.

Source entry points: [test_contracts.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_contracts.py?type=file&root=%252F), [test_nutrition.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_nutrition.py?type=file&root=%252F), and [test_food_service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/integration/test_food_service.py?type=file&root=%252F). The recorded M1 developer handoff/evidence is [001-persist-food-entry-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-developer.md?type=file&root=%252F).

Independent evidence is in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F), with retained probes in [test_w001_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w001_independent.py?type=file&root=%252F). Its closeout addendum distinguishes the reviewed source from later documentation and evidence packaging.

W002 evidence is in [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F), including its original receipt failure and passing recheck. Additional retained checks are in [test_w002_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w002_independent.py?type=file&root=%252F). The original probe and the separately hashed retention copy are both preserved.

## Coverage by layer

| Layer | Evidence expected | Current state |
| --- | --- | --- |
| Contract | Closed shapes, malformed inputs, candidate scope, source/revision guards, generated-schema drift. | Executable suite exists; not a substitute for stateful checks. |
| Nutrition/domain | Independently calculated scaling and aggregation; units/basis; bounds; unknowns; rounding and overflow boundaries; recipe yield. | Nine product-food arithmetic tests plus database overflow/unknown-value checks. Recipe arithmetic remains authored-fixture coverage only. |
| Persistence/application | Real PostgreSQL constraints and transactions; current pointers; idempotency; concurrent work; fault injection; process restart; ownership. | 38 integration checks cover M1 plus W002 transport; 16 retained QA checks cover both slices. Independent W002 review passed after the recorded receipt fix/recheck. |
| Conversation | Intent distinctions, pending state, mixed messages, target ambiguity, corrections/undo, source dates, dependent actions. | Authored expected examples exist; executable flows planned for M2. |
| LLM evaluation | Fixed annotated cases, held-out cases, reproducible provider/model/prompt/schema versions, measured intent/argument/clarification errors. | Not run; Nebius Token Factory selected in D009. Exact model, schema compatibility, and thresholds remain unverified. |
| Transport/scheduler | Authenticated ingress; outbox recovery; uncertain sends; stale callbacks; dinner/21:00 races; DST and date-bound responses. | Private Telegram ingress and sending adapters exist, with synthetic protocol tests and real-database recovery checks. No live bot or scheduler checks have run. |
| Personal release | End-to-end scenarios, startup/deployment, monitoring redaction, backup/restore, agreed export/deletion and retention behavior. | Not run; M6. |

The original 27 behavioral scenarios are preserved in [scenarios-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/scenarios-v1.md?type=file&root=%252F), with explicit coverage limits. The user-authored real-life Russian evaluation corpus is [real-life-evals-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/real-life-evals-v1.md?type=file&root=%252F). Both are inputs to test design, not completed QA reports.

## Required regression families

These are coverage categories, not a duplicate of every test case. Add executable regression cases as the corresponding layer becomes available, using requirement IDs in test names or case metadata where practical.

| Family | Requirements | Cases to preserve |
| --- | --- | --- |
| Intake and correction | FOOD-001–FOOD-005, DATA-002 | Clear item, 100 g → 80 g same entry, additional portion, plan/question non-consumption, undo, duplicate delivery versus a new identical message. |
| Clarification | FOOD-002/FOOD-004 | Save clear soup while bread waits; answer adds only bread; pending correction retains old values; unrelated weight input does not answer a food question; delayed answer retains original date. |
| Nutrition | CALC-001/CALC-002 | Known/partial/unknown nutrients, edible versus gross/bones, raw/cooked and volume/mass compatibility, finite decimal bounds, independently calculated totals. |
| Recipes | RECIPE-001–RECIPE-003 | Original ingredient amounts/instructions retained; per-100-g calculation; required yield; no default portion/batch; saving recipe is not eating; historical source versions stay pinned. |
| Observations | OBS-001/OBS-002 | One daily weight/steps slot; replacement; identical-value no-op; explicit increment once; zero versus missing; conflict/backdating. |
| Completion/check-in | DAY-001–DAY-003 | Closure suppresses completion action; missing steps allow closure; late food keeps completeness; dinner then 21:00 and fallback then dinner yield one logical offer; next-day activity reply targets prompted date. |
| Isolation/recovery | DATA-001–DATA-003 | Foreign-user references rejected; before/after-commit failure; replayed increments; stale versions; process restart; current-pointer integrity; privacy-safe operational logs. |
| Replies and reports | FOOD-006, CALC-002, UX-001 | Committed entry plus fresh day totals, visible pending/partial coverage, no false zero-intake day, complete-day denominators, nonjudgmental language. |

The existing 20 authored examples are indexed by [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F). The 50-case real-life corpus is a versioned development evaluation set, not a hidden holdout. Preserve the distinction from an unpublished held-out evaluation set: cases used in prompts or implementation tuning must not also be presented as unseen evaluation cases.

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
