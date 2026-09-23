# Russian interpretation evaluation v1

Status: instrument complete and self-tested offline; six live batches plus v3 and v4 single-case attempts were recorded 2026-09-23 as exploratory developer evidence (not independent QA). The evaluator was hardened at `5ecc774` before the latest four batches. Candidate prompts v3 and v4 and a provider runtime quality guard are prepared; the next scored live A/B run is pending. Thresholds approved by the product owner.
Owner: product owner approves rubric/thresholds; lead assistant/QA maintains the instrument and records runs.

## What this validates

Hypothesis #1: can the live model turn casual Russian food messages into correct structured proposals. This set scores the model's raw `ParserOutput` (the interpretation layer), not the deliberately bounded resolver. It is the measurement instrument the constitution requires when it states that live-model quality needs measured evaluation, not just valid JSON.

## Instrument

- [interpretation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/interpretation_v1.json?type=file&root=%252F) — the nine real Russian cases from [food_intake_calculation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/food_intake_calculation_v1.json?type=file&root=%252F), each with the parser context (candidates/recipes) and a draft rubric of signals objectively checkable from `ParserOutput`.
- [run_interpretation_eval.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/run_interpretation_eval.py?type=file&root=%252F) — batch runner. `--parser stub` self-tests offline; `--parser nebius` performs one live call per case; `--prompt PATH` A/B-tests a candidate system prompt; `--json` emits per-case raw `ParserOutput` for diagnosis; `--render-json PATH` renders a saved report without making parser calls.

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

## Second live batch — user-supplied human-readable output

The user then supplied a human-readable batch table with the same nine-case instrument. It has the same case-pass rate but different unavailable cases and quality rates: INTAKE-005 and INTAKE-007 were unavailable, while INTAKE-008 returned three actions and failed quantity extraction. The table does not include a new parser fingerprint, model id, repository revision, or raw JSON, so it is retained as a separate run rather than merged with the first scorecard.

```text
case         pass  #food  clar?  checks / notes
------------------------------------------------------------------------------
INTAKE-001   no    6      no     FAIL: quantities [gaps:2]
INTAKE-002   yes   1      no     OK
INTAKE-003   no    3      no     FAIL: clarification,clarification_paths [gaps:1]
INTAKE-004   yes   2      no     OK [gaps:1]
INTAKE-005   ERR   -      -      ParserUnavailable: Nebius request unavailable
INTAKE-006   yes   1      no     OK [gaps:1]
INTAKE-007   ERR   -      -      ParserUnavailable: Nebius request unavailable
INTAKE-008   no    3      no     FAIL: quantities [gaps:1]
INTAKE-009   no    1      no     FAIL: clarification,clarification_paths [gaps:1]

Aggregate (rate (n)):
  case pass rate        0.33
  consumed intent       1.00 (7)
  add_food count        1.00 (7)
  clarification recall  0.00 (2)
  clarification specif. 1.00 (2)
  quantity extraction   0.71 (7)
  candidate selection   1.00 (7)
  max_add_food respected 1.00 (4)
  errors                2
```

The difference between the two temperature-zero batches is itself a finding: the current evidence does not establish repeat stability. The second table is user-run exploratory evidence, not independent QA.

## Evaluator hardening — revision 5ecc774

The runner was strengthened before the next live calls. A scored action now needs a non-trivial evidence excerpt that occurs in the source, and a date hint must be absent unless the case contains date evidence and the hint quotes that evidence. Candidate selection must contain only allowed references, rather than merely containing one expected reference. These checks make the case-pass score stricter and expose malformed proposals that previously looked acceptable by count alone.

## Third live batch — strict evaluator, JSON output — 2026-09-23

The user ran the production prompt with parser fingerprint `nebius:d39eae6d90b4b4d33b80a8ca09d4cee68b45718a274a9406dee5f92f4ef0fbf0`. The JSON output records eight validated proposals and one `ParserUnavailable` (`INTAKE-007`). All eight validated proposals failed both new per-action gates: evidence spans were one-character fragments and date hints were the invented text `"2"`. The scorecard was case-pass `0.00`, evidence-valid `0.00 (8)`, date-hint-valid `0.00 (8)`, clarification accuracy `0.40 (5)`, quantity extraction `0.75 (8)`, candidate selection `0.88 (8)`, and errors `1`.

This is a stronger diagnosis than the earlier permissive runs: the model is emitting schema-valid JSON, but the proposal evidence and date fields are systematically unusable. INTAKE-005 also selected an invalid candidate set under the stricter selection rule. The run remains user-run exploratory evidence, not independent QA.

## Fourth live batch — strict evaluator, human-readable output — 2026-09-23

The human-readable command made another nine-call request, so it is a separate batch from the preceding JSON command. All nine calls returned proposals, but every case failed the evidence and date-hint gates. Its scorecard was case-pass `0.00`, evidence-valid `0.00 (9)`, date-hint-valid `0.00 (9)`, clarification recall `0.00/3`, quantity extraction `0.78 (9)`, candidate selection `0.89 (9)`, max-action compliance `1.00 (5)`, and errors `0`. This confirms the evidence/date defect is repeatable while provider availability remains variable.

## Candidate prompt v2 — two strict live batches — 2026-09-23

The user A/B-tested [prompt_candidate_v2.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v2.txt?type=file&root=%252F) with parser fingerprint `nebius:132a2f3d9d75146b4fdd9841cfe8e243117f51968502d3673cc938e88c6db545`. Each CLI command made a separate nine-call batch; the supplied JSON and human-readable outputs therefore represent two runs.

| Dimension | Candidate JSON batch | Candidate human-readable batch |
| --- | ---: | ---: |
| Case pass rate | 0.00 | 0.00 |
| Evidence validity | 0.00 (9) | 0.00 (9) |
| Date-hint validity | 0.00 (9) | 0.00 (9) |
| Clarification recall | 0.33 (3) | 0.67 (3) |
| Clarification specificity | 1.00 (3) | 1.00 (3) |
| Quantity extraction | 0.89 (9) | 1.00 (9) |
| Candidate selection | 0.56 (9) | 0.67 (9) |
| Errors | 0 | 0 |

Candidate v2 improves the intended uncertainty behavior and quantity handling compared with the strict production batches: clarification recall rises from 0.00 to 0.33–0.67, and quantity extraction rises from 0.75–0.78 to 0.89–1.00. It does not improve evidence or date hints, and it reduces exact candidate selection because the model often emits one-character food names instead of the supplied c-tokens. The candidate prompt is not ready for promotion.

## Candidate prompt v3 and provider guard — prepared 2026-09-23

[prompt_candidate_v3.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v3.txt?type=file&root=%252F) adds explicit instructions that source-backed evidence must be a contiguous excerpt of at least three characters, `date_hint.text` must be `null` without a literal date phrase, and a resolved product/recipe must use the exact supplied c-token. Short clarification replies such as `5%` remain allowed as evidence.

The generated parser schema now requires at least three characters for source-backed action evidence while keeping short clarification/cancellation evidence valid. The Nebius adapter retains a runtime guard for defense in depth and rejects non-source date hints before resolution. It exposes only bounded rejection reasons where schema validation does not already stop the response; model text and payloads remain redacted. Candidate references remain scoped by the existing context validator; unresolved name fallback remains available for cases where no supplied candidate establishes identity. Focused and full offline checks pass on the implementation revision.

## Candidate prompt v3 — single-case rejection — 2026-09-23

The user ran `INTAKE-001` with parser fingerprint `nebius:59378dac5158660ec5a32b4ec30a17b294fc8edcedd60cdb1b48a32d22e81153`. The call returned `ParserRejected: Nebius proposal failed local schema validation`, so no proposal was scored. This confirms that the model response reached the adapter but did not conform to the regenerated contract; the exact field remains redacted. The result is consistent with earlier one-character evidence fragments, but does not by itself prove that evidence was the sole schema violation. Do not spend a full batch until the prompt/model or contract diagnostic path is selected.

## Candidate prompt v4 — prepared for single-case rerun — 2026-09-23

[prompt_candidate_v4.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v4.txt?type=file&root=%252F) condenses v3 and adds one complete valid `add_food` JSON example. It keeps the strict evidence, date, exact c-token, unresolved-field, and no-arithmetic rules while reducing competing prose. It is a prompt experiment only; the shared contract and runtime guard are unchanged. Run `INTAKE-001` only, then compare whether the response passes local schema validation before considering a full batch or another model.

The user ran `INTAKE-001` with v4 and again received `ParserRejected: Nebius proposal failed local schema validation`. The compact prompt therefore did not resolve the failure for `Qwen/Qwen3-30B-A3B-Instruct-2507`; no full v4 batch was run. The next experiment is a single case against another model ID confirmed by the provider's model list.

## Alternative model single-case probes — 2026-09-23

The user ran the same v4 prompt and `INTAKE-001` against three candidate IDs:

| Model | Result | Interpretation |
|---|---|---|
| `Qwen/Qwen3-235B-A22B-Instruct-2507` | `ParserRejected: Nebius proposal failed local schema validation` | The larger Qwen model shows the same structured-proposal failure as Qwen 30B. |
| `meta-llama/Llama-3.3-70B-Instruct` | HTTP `403` | The model is not permitted for this project; no quality result. |
| `deepseek-ai/DeepSeek-V3-0324` | HTTP `404` | This model ID is unavailable; no quality result. |
| `openai/gpt-oss-120b` | `ParserRejected: Nebius proposal failed local schema validation` | This general instruction model also failed the same local contract gate. |

Parser fingerprints were `nebius:296f39d6b9666f616f007abe08a66c568998b138821b3ecb3a6dc4cbb5a6e099`, `nebius:9a521cb7901b724312334bb6bfa612709cb5fe1a695cf9d268fe08f9e9b22c33`, `nebius:5f5309068e0146636e1997661a2669f474ed73c9e173625912959138d1aa9af2`, and `nebius:456fafe3ce87ea87e82dec261236e3178af8d4f5252975bb2b0767f1ba9ea969` respectively. No candidate passed schema validation, and no full batch was run. The adapter now has a redacted field-level schema diagnostic for the next single probe.

## Findings

The seven returned proposals preserved consumption intent and included an expected candidate, but the aggregate result is below the draft quality bars. Failures are concentrated in uncertainty handling and action discipline:

1. **No clarifications raised.** In the first batch, recall was 0/3; in the second, the two scored required cases also had recall 0/2 because INTAKE-005 was unavailable. INTAKE-003 (cafeteria/bone-vs-edible and sauce) and INTAKE-009 (gross meat weight needs an edible basis) were answered silently. This threatens FOOD-002 and the “do not silently choose / do not assume portions” principles.
2. **INTAKE-001 is structurally unreliable despite valid JSON.** It returned six actions, one-character evidence spans, an invented date hint (`"2"`), and incorrect quantities instead of preserving the stated meal items and total quantities.
3. **Unavailable calls are not stable across batches.** INTAKE-007 and INTAKE-008 failed in the first batch; INTAKE-005 and INTAKE-007 failed in the second. The affected cases need targeted reruns before interpreting their model behavior.
4. **The strengthened evaluator exposes a systematic evidence/date defect.** Every action in all strict production and candidate-v2 batches used a one-character evidence span and the invented date hint `"2"`, so all cases failed those gates. This is a model/prompt failure, not a transport failure.
5. **Candidate v2 helps clarification but harms identity selection.** Its required-case recall improved to 0.33–0.67, but candidate selection fell to 0.56–0.67 because the model returned names or omitted allowed references. The next prompt must make the c-token requirement explicit and show a complete multi-action example.

The clarification and action-discipline failures are prompt-alignment hypotheses, not evidence of a model-capability ceiling. The two provider errors are operational evidence only.

## Prompt iteration plan

Candidate prompt [prompt_candidate_v2.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/prompt_candidate_v2.txt?type=file&root=%252F) remains a historical comparison. Do not promote v2. Run v3 against the production prompt only after capturing the new parser fingerprint and revision, then compare clarification recall, quantity extraction, evidence/date validity, exact candidate selection, and parser rejection counts.

## Limits and next work

- n=9 per batch, temperature 0; two permissive production batches, two strict production batches, and two strict candidate-v2 batches are recorded. Evidence/date validity remained zero in all strict batches; provider availability and quality rates varied, so repeat stability is not established.
- Nine cases validate the instrument and give a first signal; they do not select a model or certify quality. Expand the corpus (corrections/undo, plans-vs-consumption, dates/history boundaries, observations) as a held-out set separate from prompt-development cases.
- Two context/schema gaps surfaced, tracked as product decisions, not model failures: personal shortcuts ("кофе как обычно") belong in the DB and need a context slot; history references ("тот же что раньше") resolve by a 2–4 day lookback and need a context slot. These affect INTAKE-001/005 (coffee) and INTAKE-007 (cheese), currently carried as `known_gaps`. See Q04 and Q09 in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F).
