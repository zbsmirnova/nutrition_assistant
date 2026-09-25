# W027 — Local MVP gate verification

Revision: `71df815` (`Complete MVP validation scenarios`).
Date: 2026-09-25.
Role: developer verification by the lead assistant.
Independent QA review: the retained QA suite passed; no separate reviewer
performed a review specifically of this revision.

## Environment

- Python: project `.venv` (Python 3.14)
- PostgreSQL: local disposable schemas
- Alembic migration head: `0010`
- Catalog: owner-scoped synthetic product and saved recipe fixtures
- External lookup: disabled in the production worker path
- Live Nebius and real Telegram calls: not part of this local run

## Scenario coverage

| W027 scenario | Evidence in tests | Result |
| --- | --- | --- |
| W027-01 exact seeded product | `test_clear_message_saves_expected_nutrition_and_replays_once`; `test_bounded_food_reconciles_central_and_daily_ranges` | pass |
| W027-02 saved recipe by eaten grams | `test_saved_recipe_is_an_opaque_candidate_and_logs_eaten_grams` | pass |
| W027-03 multiple meals and daily reconciliation | `test_multiple_meals_reconcile_to_one_current_day_total` | pass |
| W027-04 100 g → 80 g correction | `test_recipe_quantity_correction_updates_eaten_grams`; service correction identity tests | pass |
| W027-05 replay and worker restart | replay tests and `test_real_process_crashes_resume_before_and_after_frozen_command_and_domain_commit` | pass |
| W027-06 pre/post commit failure recovery | `test_real_process_crash_before_commit_keeps_result_and_response`; `test_real_process_crash_after_commit_keeps_result_and_response` | pass |
| W027-07 current and previous-date readback | `test_day_readback_is_durable_and_uses_the_same_worker_pipeline` | pass |
| W027-08 unknown product outside totals | `test_unknown_product_without_external_lookup_is_visible_and_outside_totals` | pass; restaurant remains excluded by scope |
| W027-09 weight and steps | `ObservationTests` set/replace/increment and separate-date checks | pass; reported separately |

## Acceptance results

- 124 offline contract/unit tests passed.
- 110 PostgreSQL integration tests passed.
- 32 retained independent QA tests passed.
- `git diff --check` passed.
- Accepted food operations are durable and replay-safe in the local worker
  path; corrections preserve entry identity and revisions.
- Daily kcal/protein/fat/carbohydrate totals reconcile with committed entries,
  including bounded nutrition snapshots.
- Unknown products now produce a durable visible clarification and do not alter
  totals. The production path does not call external catalogs.

## Limits and next step

This verifies the implementation and local persistence gate. It does not prove
Nebius Russian-language interpretation quality, live Telegram polling/delivery,
or deployment availability. Those are the next E2E checks. Telegram product
creation, restaurant estimates, reminders, progress reports, and other
post-gate lanes remain outside W027. Live user-run observations are tracked in
[027-live-e2e-notes.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/027-live-e2e-notes.md?type=file&root=%252F).
