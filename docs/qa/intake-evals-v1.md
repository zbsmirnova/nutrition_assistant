# Intake evaluation draft v1

Status: authored from user-provided real-life cases; fixture values and live execution are pending.
Owner: product owner supplies behavior; QA/lead assistant maintains the executable representation.

[intake_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/intake_v1.json?type=file&root=%252F) records the nine agreed intake cases. A case is a reproducible episode: user turns, explicit fixture requirements, expected interpretation/resolution/persistence/calculation behavior, and prohibited behavior.

## How this set is scored

Score three layers separately. The interpreter must extract the intended food, quantity, user reference, preparation detail, or needed clarification. The application must resolve only the required user-scoped recipe/product/history source. The deterministic nutrition engine must calculate using the source/version selected by the application and preserve unknowns and estimates.

The corpus intentionally does not contain invented kcal or macro values. Before numeric scoring, create synthetic fixture records for every `fixtures` identifier in the corpus, including exact per-100-g nutrition, recipe versions, usual-coffee contents, a standard physalis weight, history state, and the configured recent-meal window. Expected numeric values are then generated independently from those frozen fixture records. This prevents an evaluation from silently treating arbitrary catalogue choices as correct.

## Current limits

These nine cases are sufficient to validate the annotation format and start a food-intake regression suite. They are not enough to select a live model or establish end-to-end quality. Add separate cases for plans versus consumption, corrections/undo, recipe version updates, labels and partial macros, ambiguous references, date/history boundaries, daily totals and closure idempotency, observations, persistence failures, and multi-turn clarification answers. Keep later development examples separate from a held-out model-selection set.
