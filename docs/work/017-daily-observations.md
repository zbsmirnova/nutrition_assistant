# W017 — Daily body weight and steps observations

Status: done.
Milestone: M4.
Owner: lead assistant, architect/developer.
Updated: 2026-09-24.
Decision: D029, under D004 and OBS-001/OBS-002.

## Outcome and scope

Persist one revisable body-weight value and one revisable steps total per user and local date, with revision history and ownership checks. Support setting weight, setting an absolute steps total, and adding an explicit steps increment when a starting total is known. Backdating uses the command's effective date. A missing steps value and an explicitly recorded zero are distinct. Confirmations are in Russian.

Example: "Вес 76.3 сегодня" then "76.1" leaves one current value of 76,1 кг with 76,3 retained in history; "8200 шагов" then "ещё 500" yields a current total of 8700 recorded as an increment.

## Requirements and decisions

OBS-001, OBS-002; D004 (one daily weight/steps value with history, explicit increments, missing-vs-zero); D029 (physical two-table observation model and command semantics); section 8 of the data model. The typed `set_daily_weight`, `set_daily_steps`, and `increment_daily_steps` commands and the `WeightSnapshot`/`StepsSnapshot` results already existed in the M0 contracts and are unchanged. Deletion/undo of observations, Apple Health reconciliation, live-day observation summaries, and the combined check-in (W018) are out of scope.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W017-A01 | Setting a weight or steps value creates one daily slot and an initial active revision, returning the resulting snapshot; a later value on the same date adds a revision, updates the current value, and retains history in one slot. |
| W017-A02 | A set command must state the exact current revision it replaces, or none when no value exists; a stale or absent expected revision is a revision conflict with no mutation. |
| W017-A03 | Re-setting the identical active value is a `same_value` no-op, not a new revision. |
| W017-A04 | An explicit steps increment adds to a known active total, records `origin_kind = increment`, and is rejected when no starting total exists. |
| W017-A05 | A missing steps observation and an explicitly recorded zero are distinguishable; weight and steps coexist on the same date; backdating targets a separate daily slot. |
| W017-A06 | Observations are user-scoped: one user cannot see or replace another user's daily values, enforced by composite ownership keys and the user mutation lock. Duplicate delivery/operation replay does not add a revision. |
| W017-A07 | Committed weight and steps outcomes render Russian confirmations, including a no-change acknowledgment. |

## Implementation checklist

- Migration 0009 adds `observations` and `observation_revisions` with per-metric value/unit checks, revision-ownership uniqueness, a deferred current-revision foreign key, and a date-range index. — done
- Schema model in `nutrition_app/schema.py` mirrors the migration; drift test asserts parity. — done
- Service handlers `_set_weight`, `_set_steps`, `_increment_steps`, a `get_observation` read helper, plus validation/dispatch. — done
- Russian rendering `render_observation_result` and a `render_result` dispatcher; Telegram sender uses the dispatcher. — done
- PostgreSQL integration tests in `tests/integration/test_observation_service.py`. — done
- Conversation resolution maps parser observation proposals to trusted backend commands; the backend supplies the source-local date and current revision guard, while private revision IDs remain outside provider context. — done
- The bounded Telegram worker now accepts `set_daily_weight`, `set_daily_steps`, and `increment_daily_steps` proposals and executes them through the existing observation service. — done

## Acknowledgment copy

The MVP weight acknowledgment is `Вес за сегодня записан: 76,3 кг.`. The
confirmation intentionally uses the current-day wording while the stored
observation date and revision history remain unchanged. Steps keep their
dated confirmation wording for now.

## Developer handoff

Setup: install pinned runtime dependencies and start local PostgreSQL per the README, then run the checks below. The observation persistence slice changed `nutrition_app/schema.py`, `nutrition_app/service.py`, `nutrition_app/rendering.py`, `nutrition_app/telegram.py`, `nutrition_app/demo.py`, `migrations/versions/0009_daily_observations.py`, and the observation/food integration tests. The follow-up resolver slice changed `nutrition_app/interpretation.py`, `nutrition_app/conversation.py`, `tests/test_interpretation.py`, and the simulated Nebius worker fixture in `tests/integration/test_nebius_worker.py` so it follows the backend-derived-evidence provider contract. Migration: `alembic` upgrade to head (0009) via the standard `migrate` path; PostgreSQL suites run it on disposable schemas. No contract model changed, so schema regeneration was not required. Earlier developer checks on 2026-09-24 covered 115 offline tests, 97 PostgreSQL integration tests, and 32 retained QA tests. The MVP acknowledgment follow-up then passed 118 offline tests, 103 PostgreSQL integration tests, 32 retained QA tests, and `git diff --check`; exact revision evidence is recorded in [018-mvp-acknowledgment-rendering-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/018-mvp-acknowledgment-rendering-developer.md?type=file&root=%252F). The user confirmed live Telegram processing of an absolute steps value followed by an explicit increment, with the final daily total correct after the queued messages were drained; exact personal measurements are intentionally omitted here. Known limitations: no observation deletion/undo, no live-day observation summary, and no check-in yet.

## QA result and completion

Developer verification only; recorded in [017-daily-observations-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/017-daily-observations-developer.md?type=file&root=%252F). No independent QA review was run. Definition of done: all acceptance criteria observable through the retained tests, offline and both PostgreSQL suites green, and the migration/model parity check passing. Live Telegram observation processing is now confirmed by the user for set and increment behavior; live model coverage and broader conversational behavior remain outside this brief.
