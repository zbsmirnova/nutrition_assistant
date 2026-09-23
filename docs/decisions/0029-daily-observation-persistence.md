# D029 — Persist revisable daily body weight and steps observations

Kind: technical
Status: accepted for W017
Recorded: 2026-09-23.
Decision owner: architect under the accepted observation model D004 and OBS-001/OBS-002.

## Decision

Daily observations use a generic two-table shape restricted to two v1 metrics. `observations` holds a stable per-metric daily slot with a unique `(user_id, metric, series_date)` and a current-revision pointer; `observation_revisions` holds immutable revisions with the measured `value`, `unit`, `local_date`, `time_zone`, `state`, and an `origin_kind` of `manual` or `increment`. A deferred composite current-revision foreign key proves the current revision belongs to that observation and user, matching the M1 food/product/recipe pattern. Migration 0009 adds both tables, the per-metric value/unit check constraints, revision-ownership uniqueness, and a date-range index.

The backend serializes each user's mutations under the existing user-row lock, so observation handlers need no extra row locks. Three resolved commands are supported: `set_daily_weight`, `set_daily_steps`, and `increment_daily_steps`. A set command must state the exact current revision it replaces (`expected_revision_id`), or `null` when no value exists yet; a mismatch is a revision conflict. Re-setting the identical active value is a `no_change`/`same_value` no-op rather than a new revision. An increment requires a known active starting total and adds to it, recording `origin_kind = increment`. Backdating is a normal `effective_date` on a separate daily slot. A missing observation and an explicitly recorded zero are distinct: no slot means no measurement, while an active steps revision with value `0` is a recorded zero.

## Consequences

Weight and steps share a date without collision because the slot is keyed by metric. History is preserved for replacements and increments, and current views read only the active current revision. Define/replace/increment operations are idempotent through the existing prepared/applied operation path and outbox response intent. The generic shape deliberately excludes training, cycle, or extra activity fields; new metrics require explicit validation and product scope (Q07). Deletion/undo of observations, Apple Health import reconciliation, and the combined check-in remain later work.

## References

[0004-revisions-recipes-observations.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0004-revisions-recipes-observations.md?type=file&root=%252F), OBS-001/OBS-002 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), section 8 of [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F), and [017-daily-observations.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/017-daily-observations.md?type=file&root=%252F).
