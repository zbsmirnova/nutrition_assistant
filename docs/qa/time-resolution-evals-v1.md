# Time-resolution evaluation draft v1

Status: authored from user-provided cases; not executed against a live model.
Owner: product owner supplies behavior; QA/lead assistant maintains the executable representation.

[time_resolution_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/time_resolution_v1.json?type=file&root=%252F) defines four Russian food-message date cases. All share a Europe/Berlin message-local date of 2026-09-23 and a pre-resolved synthetic food identity, so the evaluator can score date handling without confusing it with dairy-product clarification.

The model is scored on extracting either no date hint, `вчера`, `20 сентября`, or `три дня назад`. The backend is scored independently on applying that hint to the captured message-local date. A delayed worker must never substitute its processing date. An explicit Russian date phrase is evaluated only in the supplied unambiguous calendar context. `Три дня назад` is deliberately a clarification case whenever that expression is unsupported or ambiguous: no food may be saved under an inferred date.

Current W003 resolution supports no date, `вчера`, and ISO dates in its bounded controlled-parser path; it deliberately defers unsupported expressions and does not yet send interactive clarification questions. The written-date and clarification expectations are future conversation behavior. These cases therefore measure the target contract, not a claim that every case is implemented today.
