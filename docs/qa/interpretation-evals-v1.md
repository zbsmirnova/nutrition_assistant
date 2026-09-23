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

Executed by the user's terminal holding `NEBIUS_API_KEY`; this environment never received the secret. Repository revision: `f983feb4f38510dd06fd26d5978af15b87a468cc`. Model: `Qwen/Qwen3-30B-A3B-Instruct-2507`. Parser fingerprint: `nebius:d39eae6d90b4b4d33b80a8ca09d4cee68b45718a274a9406dee5f92f4ef0fbf0`. Nine live calls were attempted at temperature 0; seven returned validated proposals and two returned `ParserUnavailable` (`INTAKE-007`, `INTAKE-008`). This is developer/exploratory evidence, not an independent QA verdict.

| Dimension | Result | Threshold | Read |
| --- | --- | --- | --- |
| Errors | 2 / 9 | — | `ParserUnavailable` on INTAKE-007 and INTAKE-008; no schema/reference rejection was reported for the seven returned proposals |
| Consumption intent | 1.00 (7) | — | All seven returned proposals treated the source as consumed food |
| Candidate selection | 1.00 (7) | — | At least one expected candidate appeared in each scored proposal; this check does not penalize extra candidates |
| No invented items (`max_add_food`) | 1.00 (3) | — | All three cases with a maximum-action rule respected it |
| add_food count | 1.00 (7) | — | The count check passed even where the proposal contained semantically wrong extra actions |
| Quantity extraction | 0.86 (7) | ≥ 0.90 | Below bar |
| Clarification accuracy | 0.40 (5) | ≥ 0.80 | Below bar; the blended value hides the required-case failure |
| Clarification recall | 0.00 (3) | — | **Never asked** on any case that should |
| Clarification specificity | 1.00 (2) | — | Clean cases stayed silent |
| **Case pass rate** | **0.33** | **≥ 0.70** | **Below bar** |

Raw scorecard: user-provided `/tmp/interp_live.json` output (the local copy in this environment is not the source of record; regenerate with the runner).

## Findings

The seven returned proposals preserved consumption intent and included an expected candidate, but the aggregate result is below the draft quality bars. Failures are concentrated in uncertainty handling and action discipline:

1. **No clarifications raised (recall 0/3).** INTAKE-003 (cafeteria/bone-vs-edible and sauce), INTAKE-005 (паштет matches two saved recipes), and INTAKE-009 (gross meat weight needs an edible basis) were all answered silently. This threatens FOOD-002 and the “do not silently choose / do not assume portions” principles.
2. **INTAKE-001 is structurally unreliable despite valid JSON.** It returned six actions, one-character evidence spans, an invented date hint (`"2"`), and incorrect quantities instead of preserving the stated meal items and total quantities.
3. **The two unavailable calls need a repeat.** INTAKE-007 and INTAKE-008 cannot distinguish a transient provider failure from a reproducible model/request issue. They must be rerun before interpreting those cases.
4. **The evaluator is intentionally permissive in two places.** Candidate selection only requires an expected reference to appear, and `add_food_count` can pass while extra actions are semantically wrong. Evidence quality, date-hint quality, and extra candidates need stronger scoring before using this as a go/no-go gate.

The clarification and action-discipline failures are prompt-alignment hypotheses, not evidence of a model-capability ceiling. The two provider errors are operational evidence only.

## Prompt iteration plan

Candidate prompt [prompt_candidate_v2.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v2.txt?type=file&root=%252F) targets exactly these faults without touching the production prompt: it requires an unresolved clarification for missing/ambiguous fields (no-quantity items, multi-recipe names, gross meat weight), forbids dropping a mentioned item, and forbids the model from splitting a stated total by ratio. Next step: A/B it live against the production prompt via `--prompt`, then promote to `nebius_prompt.txt` only if it lifts clarification recall and fixes the splits **without** regressing identity (1.00), intent (1.00), or the no-invented-items guard.

## Limits and next work

- n=9, one run, temperature 0, with two unavailable calls — no repeat-stability measurement yet.
- Nine cases validate the instrument and give a first signal; they do not select a model or certify quality. Expand the corpus (corrections/undo, plans-vs-consumption, dates/history boundaries, observations) as a held-out set separate from prompt-development cases.
- Two context/schema gaps surfaced, tracked as product decisions, not model failures: personal shortcuts ("кофе как обычно") belong in the DB and need a context slot; history references ("тот же что раньше") resolve by a 2–4 day lookback and need a context slot. These affect INTAKE-001/005 (coffee) and INTAKE-007 (cheese), currently carried as `known_gaps`. See Q04 and Q09 in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F).
