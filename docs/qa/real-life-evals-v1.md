# Real-life Russian conversation evaluations v1

Status: authored development evaluation corpus; not executed against a live model.
Owner: QA/lead assistant. Updated: 2026-09-22.

The user supplied 50 real-life Russian scenarios. Their normalized, machine-readable form is [real_life_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/real_life_v1.json?type=file&root=%252F). The corpus is the source for this document's case IDs and expected results; it deliberately does not duplicate a second test script.

## Purpose and use

Use `RL-001` through `RL-050` to assess a future live Russian-language interpreter and the complete downstream agent behavior. Provide every case's `preconditions` as explicit test context. Score its `effects` and `invariants` independently: an invariant failure is a failed case even when the broad intent is correct. For stateful continuations, run only the listed dependency chain in one isolated owner/date fixture.

The corpus covers food interpretation, uncertainty, saved recipes and versions, partial nutrition, daily totals/history/closure, observations, alcohol and cooking questions, future training behavior, and durable-write failure disclosure. It preserves a user-selected coffee follow-up rule as profile context; it is not a global inference that breakfast always includes coffee.

`scope` makes the present boundary explicit:

- `future_v1` describes accepted or user-directed behavior that still needs a scoped implementation slice.
- `v2` is training functionality. The current constitution places training after v1, so these cases are retained for future planning and must not be counted as an M2 result.

Cases `RL-048`–`RL-050` name a configured primary store and optional file export rather than prescribing SQLite or a particular Library product. The current implementation uses PostgreSQL and has no CSV/Library synchronizer; the behavioral requirement is confirmed, accurately disclosed durable writes.

## Evaluation protocol

1. Freeze the corpus version, model ID, prompt version, parser schema version, catalog/profile fixture, and application revision.
2. Use synthetic owners, recipes, products, history, and messages. Do not place real personal messages or credentials in the corpus or results.
3. First run these cases as a development set. Keep a separate, unpublished annotated holdout for model-selection claims after prompt or resolver tuning uses this corpus.
4. Report per-case result, failed effects/invariants, refusal/clarification quality, parser-output validity, and downstream mutation/result behavior separately. A correct response text is insufficient if the backend writes the wrong record.
5. Do not report an aggregate accuracy threshold until Q09 resolves model-selection criteria. Never call an unrun corpus a live-model result.

## Present coverage boundary

W003 only executes controlled single-product additions and dairy deferral. None of these 50 cases has been executed against Nebius or a live Telegram conversation. The corpus extends [scenarios-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/scenarios-v1.md?type=file&root=%252F); it does not replace the stable `S01`–`S31` inventory or any work brief's acceptance criteria.
