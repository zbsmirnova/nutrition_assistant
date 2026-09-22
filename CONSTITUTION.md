# Product constitution

Status: maintained product baseline. Recorded 2026-09-22.
Owner: product owner for product choices; lead assistant for maintenance.

## Idea and intended user

Build a personal Telegram assistant that makes food, recipes, body weight, and daily steps easy to record in ordinary Russian conversation. Give the user understandable nutrition totals, correctable records, and useful history without moralizing. Start with personal use while designing ownership boundaries for possible future users; the access mechanism is part of the architecture design.

The original architecture brief is historical input. Later explicit decisions in the product discussion govern where they differ: continuous food saving, optional completion, 21:00 fallback, the simplified recipe model, one daily weight/steps value, and training in v2.

## Goals

- Reduce effort for incremental food logging and later corrections.
- Calculate kcal, protein, fat, and carbohydrates consistently, with visible uncertainty and provenance.
- Preserve records across retries and restarts without inventing duplicate consumption.
- Keep day completeness, nutrition coverage, and missing activity distinct.
- Support repeat cooking from saved recipe ingredients/instructions and nutrition per 100 g.
- Keep personal data scoped to its owner and make future export/deletion choices implementable.

No numerical usability, accuracy, cost, or latency target has been agreed. Live-model quality requires measured evaluation, not just valid JSON.

## Scope

Accepted v1 domains: food logging and corrections, recipes, one daily body weight, one daily steps total, and the optional combined completion/activity check-in. Personal products and manual nutrition values support food logging. The release roadmap includes history/reporting and operational readiness; report scheduling and export/deletion requirements still have open product details.

Training/workout tracking belongs in v2. Other measurements, menstrual-cycle context, additional activity metrics, Apple Health integration, external catalog/barcode conveniences, habit suggestions, historical imports, and public multi-user access are future work with timing to be decided.

V1 does not include food-photo estimation, medical advice, autonomous changes to production code, or a promise of exact restaurant-food nutrition.

## Enduring requirements

These IDs are stable references for specifications, work briefs, and QA. Product decisions reflect the accepted discussion; calculation, ownership, and non-moralizing principles also retain the original brief's constraints. Detailed proposed edge-case defaults remain in the specifications and decision register.

| ID | Requirement |
| --- | --- |
| FOOD-001 | Save independently clear consumed-food entries continuously. A close-day action is not required to persist food. |
| FOOD-002 | Ask about material missing details, including dairy fat percentage when needed to identify the consumed product/nutrition profile. Do not ask again when the message or exact identified product/label already resolves it. Persist the pending message/action, but exclude unresolved new food from totals; an uncertain correction leaves the previously committed entry intact. An estimated portion requires explicit approval. |
| FOOD-003 | Correct the same logical entry with retained revision history; changing 100 g to 80 g must not add another portion. |
| FOOD-004 | In a mixed message, save clear independent items and clarify unresolved ones. Answering later must not repeat the already saved items. |
| FOOD-005 | Plans, questions, and product/recipe definitions are not evidence of consumption. |
| FOOD-006 | Food acknowledgments describe what was saved or corrected and show the entry nutrition plus updated day totals, including pending/partial coverage where relevant. |
| RECIPE-001 | Store versioned kcal and macronutrients per 100 g, original ingredient amounts/units, and cooking instructions when supplied. Calculate from arbitrary ingredient amounts or accept supplied per-100-g values. |
| RECIPE-002 | Store eaten grams on food entries. Do not introduce default recipe portions, serving counts, or separate cooked-batch entities. Ask for material missing calculation inputs such as usable finished yield. |
| RECIPE-003 | Product/recipe updates must not silently change historical meals. Preserve the source/version and calculation basis used by each meal. |
| OBS-001 | Keep one current body-weight value per user/local date. Later values replace it with history, rather than creating multiple current readings or an average. |
| OBS-002 | Keep one current steps total per user/local date. Later absolute totals replace it; only an explicit increment adds steps, with a known starting value. Missing steps and an explicitly supplied zero differ. |
| DAY-001 | Offer the combined completion/activity check-in after dinner, or at 21:00 local time if no dinner is recorded. Do not offer another completion button after conversational closure or a second logical check-in after a fallback followed by late dinner. |
| DAY-002 | Support “Everything logged”, “Add steps”, and “Later”. Missing steps do not prevent food completion. A closure acknowledgment can invite missing activity without another completion action. |
| DAY-003 | Late food additions update totals while preserving day completeness; no new completion confirmation or check-in is required. |
| CALC-001 | The LLM proposes interpretations. The backend owns identity, authorization, reference resolution, calculations, and durable mutations. |
| CALC-002 | Unknown nutrients are not zero. Preserve source quality, units, edible/raw/cooked basis, and available bounds. Do not infer missing fat or carbohydrate solely from total calories. |
| DATA-001 | Preserve traceability and ordinary correction history under an agreed retention policy. Revisions are not an exemption from account erasure. |
| DATA-002 | Retrying a delivery or an operation must not apply its domain mutation twice. Distinct user messages must not be deduplicated merely because their text matches. |
| DATA-003 | Scope every personal read, mutation, and reference to its authenticated owner, including recipes, sources, revisions, and pending actions. |
| UX-001 | Keep replies useful and nonjudgmental. Do not moralize food, prescribe compensation, or treat exercise as permission to eat. |

Europe/Berlin is the initial configured time zone, not a hard-coded UTC offset. Preserve the date targeted by a message or clarification; detailed resolution and scheduler behavior belong in the conversation specification.

## Boundaries and changes

Detailed interaction rules live in [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); implementation structure lives in [architecture-plan.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/architecture-plan.md?type=file&root=%252F). Open choices and their owners live in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). Do not treat a recommendation or an implemented schema as approval of unresolved product behavior.

The lead assistant maintains this document whenever an authorized change affects product scope or enduring requirements. Record consequential changes in a decision record, update affected specifications and acceptance criteria in the same work, and preserve superseded reasoning. The user should not need to repeat decisions or remind the assistant to update documentation.
