# Russian interpretation evaluation v1

Status: instrument complete and self-tested offline; first live run recorded 2026-09-23 as exploratory developer evidence (not independent QA). Thresholds approved by the product owner.
Owner: product owner approves rubric/thresholds; lead assistant/QA maintains the instrument and records runs.

## What this validates

Hypothesis #1: can the live model turn casual Russian food messages into correct structured proposals. This set scores the model's raw `ParserOutput` (the interpretation layer), not the deliberately bounded resolver. It is the measurement instrument the constitution requires when it states that live-model quality needs measured evaluation, not just valid JSON.

## Instrument

- [interpretation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/interpretation_v1.json?type=file&root=%252F) — the nine real Russian cases from [food_intake_calculation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/food_intake_calculation_v1.json?type=file&root=%252F), each with the parser context (candidates/recipes) and a draft rubric of signals objectively checkable from `ParserOutput`.
- [run_interpretation_eval.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/run_interpretation_eval.py?type=file&root=%252F) — batch runner. `--parser stub` self-tests offline; `--parser nebius` performs one live call per case; `--prompt PATH` A/B-tests a candidate system prompt; `--json` emits per-case raw `ParserOutput` for diagnosis.

Scored dimensions: consumption intent, add_food count, quantity extraction, candidate selection, `max_add_food` (no invented items), and clarification behavior reported as **recall** (of cases that should ask, how many did) and **specificity** (of clean cases, how many stayed silent). The blended clarification metric is retained but is misleading on its own.

Approved draft thresholds: case-pass ≥ 0.70, clarification ≥ 0.80, quantity extraction ≥ 0.90.

## First live run — 2026-09-23

Executed by the session holding `NEBIUS_API_KEY`; this environment never received the secret. Parser fingerprint `nebius:d39eae6d…` (the exact `NUTRITION_LLM_MODEL` id was not captured in the JSON — record it on the next run). Nine live calls, temperature 0, one run per case. This is developer/exploratory evidence, not an independent QA verdict.

| Dimension | Result | Threshold | Read |
| --- | --- | --- | --- |
| Errors (schema/context) | 0 / 9 | — | Live transport, structured-output schema wrapper, and context validation all work in practice |
| Consumption intent | 1.00 (9) | — | No food log misread as chat/plan |
| Candidate selection | 1.00 (9) | — | Correct product/recipe every case, incl. "Брезель"→"брецель" spelling tolerance |
| No invented items (`max_add_food`) | 1.00 (5) | — | Never added hidden oil (INTAKE-008/009) |
| add_food count | 0.89 (9) | — | One miss (INTAKE-004) |
| Quantity extraction | 0.78 (9) | ≥ 0.90 | Below bar |
| Clarification recall | 0.00 (3) | — | **Never asked** on any case that should |
| Clarification specificity | 1.00 (3) | — | Correctly silent on clean cases |
| **Case pass rate** | **0.33** | **≥ 0.70** | **Below bar** |

Raw scorecard: `/tmp/interp_live.json` (transient; regenerate with the runner).

## Findings

Fundamentals are strong (intent, identity, no hallucinated items). Failures concentrate on a single behavioral axis — the model does not handle uncertainty the way the product requires:

1. **No clarifications raised (recall 0/3).** INTAKE-003 (cafeteria/bone-vs-edible, sauce), INTAKE-005 (пат matches two saved recipes), and INTAKE-009 (gross meat weight needs edible weight) were all answered silently instead of marking a field unresolved. This threatens FOOD-002 and the "do not silently choose / do not assume portions" principles.
2. **Silently drops an uncertain item.** INTAKE-004 dropped "одна ягодка физалиса" (no grams) rather than emitting the item with quantity unresolved.
3. **Performs backend arithmetic (self-splitting).** INTAKE-001 and INTAKE-008 produced per-component grams by applying the stated "1:1" ratio instead of reporting the stated total (115 g / 120 g) and leaving the split to the backend — a CALC-001 division-of-labor breach, and the cause of both quantity-extraction misses.

All three are prompt-alignment problems, not evidence of a model-capability ceiling.

## Prompt iteration plan

Candidate prompt [prompt_candidate_v2.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v2.txt?type=file&root=%252F) targets exactly these faults without touching the production prompt: it requires an unresolved clarification for missing/ambiguous fields (no-quantity items, multi-recipe names, gross meat weight), forbids dropping a mentioned item, and forbids the model from splitting a stated total by ratio. Next step: A/B it live against the production prompt via `--prompt`, then promote to `nebius_prompt.txt` only if it lifts clarification recall and fixes the splits **without** regressing identity (1.00), intent (1.00), or the no-invented-items guard.

## Limits and next work

- n=9, one run, temperature 0 — no repeat-stability measurement yet; capture the model id on the next run.
- Nine cases validate the instrument and give a first signal; they do not select a model or certify quality. Expand the corpus (corrections/undo, plans-vs-consumption, dates/history boundaries, observations) as a held-out set separate from prompt-development cases.
- Two context/schema gaps surfaced, tracked as product decisions, not model failures: personal shortcuts ("кофе как обычно") belong in the DB and need a context slot; history references ("тот же что раньше") resolve by a 2–4 day lookback and need a context slot. These affect INTAKE-001/005 (coffee) and INTAKE-007 (cheese), currently carried as `known_gaps`. See Q04 and Q09 in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F).
