# Product constitution

Status: maintained product baseline. Recorded 2026-09-22.
Owner: product owner for product choices; lead assistant for maintenance.

## Idea and intended user

Build a personal Telegram assistant that makes food, recipes, body weight, and daily steps easy to record in ordinary Russian conversation. Give the user understandable nutrition totals, correctable records, and useful history without moralizing. Start with personal use while designing ownership boundaries for possible future users; the access mechanism is part of the architecture design.

The original architecture brief is historical input. Later explicit decisions in the product discussion govern where they differ: continuous food saving, independent MVP steps logging, deferred close-day/check-in behavior, the simplified recipe model, one daily weight/steps value, and training in v2.

## Goals

- Reduce effort for incremental food logging and later corrections.
- Calculate kcal, protein, fat, and carbohydrates consistently, with visible uncertainty and provenance.
- Preserve records across retries and restarts without inventing duplicate consumption.
- Keep day completeness, nutrition coverage, and missing activity distinct.
- Support repeat cooking from saved recipe ingredients/instructions and nutrition per 100 g.
- Keep personal data scoped to its owner and make future export/deletion choices implementable.

No numerical usability, accuracy, cost, or latency target has been agreed. Live-model quality requires measured evaluation, not just valid JSON.

## Scope

The first MVP validation gate covers one-user Telegram food logging and
corrections, consumption of owner-scoped products and saved recipes preloaded
through the trusted local provisioning path, durable daily totals and readback,
and the existing persistence/retry/outbox guarantees. It validates the
calculation and recording hypothesis with a small personal catalog. Weight and
steps remain supported as an adjacent capability and are verified separately;
they do not block the calorie-recording verdict. Telegram catalog growth is the
next slice: the user will add products through the bot after this validation
gate. Unknown products and restaurant dishes are a separate experiment and are
not part of the core MVP release gate. D047's uncertainty coefficients remain
the experimental policy for that lane; open-database lookup is disabled in the
validation path.

The MVP's reliable food input is one food item per Telegram message. Lists of
multiple independent food items remain a V2 slice; the current worker must not
silently save an arbitrary subset of such a list.

The combined completion/activity check-in and reminders are post-MVP W018
work. The release roadmap includes history/reporting, post-MVP feedback capture,
and operational readiness; report scheduling and export/deletion requirements
still have open product details.

Training/workout tracking belongs in v2. Other measurements, menstrual-cycle context, additional activity metrics, Apple Health integration, barcode/photo flows, open-ended restaurant source validation, background catalog synchronization, habit suggestions, historical imports, and public multi-user access are future work with timing to be decided.

V1 does not include food-photo estimation, medical advice, autonomous changes to production code, or a promise of exact restaurant-food nutrition.

## Enduring requirements

These IDs are stable references for specifications, work briefs, and QA. Product decisions reflect the accepted discussion; calculation, ownership, and non-moralizing principles also retain the original brief's constraints. Detailed proposed edge-case defaults remain in the specifications and decision register.

| ID | Requirement |
| --- | --- |
| FOOD-001 | Save independently clear consumed-food entries continuously. A close-day action is not required to persist food. |
| FOOD-002 | Ask about material missing details, including dairy fat percentage when needed to identify the consumed product/nutrition profile, preparation or subtype when it changes nutrition materially, and exact usable weight when the amount is approximate, partial, ranged, gross/edible ambiguous, bone-in, or otherwise uncertain. Examples include skin/oil for chicken, added fat for eggs, cheese type/producer, and oil for baked potatoes. Do not ask again when the message or exact identified product/label already resolves it. Persist the pending message/action, but exclude unresolved new food from totals; an uncertain correction leaves the previously committed entry intact. An estimated or assumed portion requires explicit user approval and visible provenance. |
| FOOD-003 | Correct the same logical entry with retained revision history; changing 100 g to 80 g must not add another portion. |
| FOOD-004 | For the post-MVP V2 multi-product slice, save clear independent items in a mixed message and clarify unresolved ones. Answering later must not repeat the already saved items. A quantity clarification may be answered by replying to the original food message, replying to the bot's clarification, or sending a new standalone message with natural wording such as `там было граммов 200`; the backend must bind standalone answers to the correct pending context and preserve whether the amount is exact or approximate. The MVP accepts one food item per message and keeps its current reply-linked clarification behavior. |
| FOOD-005 | Plans, questions, and product/recipe definitions are not evidence of consumption. |
| FOOD-006 | Food acknowledgments describe what was saved or corrected and show the entry's central kcal/protein estimate plus the updated daily kcal/protein range. The backend continues to persist all four nutrient fields, their bounds, pending state, and completeness; routine MVP Telegram copy omits fat/carbohydrate lines and pending/completeness notices. |
| FOOD-007 | In the MVP, model output may identify ambiguity and offer bounded choices, but user decisions control approximations, assumptions, averages, portion conversions, edible-weight interpretations, and recipe substitutes. Unapproved choices remain pending and outside totals. |
| FOOD-008 | Represent nutrition uncertainty as lower and upper bounds for kcal and all four nutrient fields. The validation slice exercises the working ±10% ordinary-food range; the ±25% restaurant range and weight-range combination belong to the separate estimate experiment. These coefficients are operational defaults, not accuracy guarantees. |
| CATALOG-001 | After the core validation gate, a user may create a personal product through Telegram. Kcal and protein are required; when fat and carbohydrates are absent, the model may propose a nearest analogue and must ask for confirmation. If the user rejects it, request the values manually and do not create an active or pending product. The first validation pass uses trusted local provisioning instead. |
| CATALOG-002 | Product-label photo and barcode lookup are future input methods; they should populate the same versioned product profile as typed label data. |
| RECIPE-001 | Store versioned kcal and macronutrients per 100 g, original ingredient amounts/units, and cooking instructions when supplied. Calculate from arbitrary ingredient amounts or accept supplied per-100-g values. |
| RECIPE-002 | Store eaten grams on food entries. Do not introduce default recipe portions, serving counts, or separate cooked-batch entities. Ask for material missing calculation inputs such as usable finished yield. |
| RECIPE-003 | Product/recipe updates must not silently change historical meals. Preserve the source/version and calculation basis used by each meal. |
| OBS-001 | Keep one current body-weight value per user/local date. Later values replace it with history, rather than creating multiple current readings or an average. |
| OBS-002 | Keep one current steps total per user/local date. Later absolute totals replace it; only an explicit increment adds steps, with a known starting value. Missing steps and an explicitly supplied zero differ. |
| REPORT-001 | Post-MVP reporting may provide concise weight-trend feedback by comparing the current value with available measurements from the previous 4–7 local days; exact coverage and wording are decided in M5. |
| REPORT-002 | The first post-MVP reporting slice is on-demand, read-only progress questions in ordinary Telegram language. Automatic scheduled feedback reuses the same report service later. |
| MVP-001 | The core validation gate must preserve each accepted food operation exactly once across retries and restarts, retain same-entry correction history, and reconcile daily totals with committed entries. |
| MVP-002 | The owner must be able to read a current day/date summary after processing and restart; this readback is a stability check, not a progress-reporting feature. |
| MVP-003 | Unknown-food and restaurant estimation, external catalog lookup, and Telegram catalog authoring are separate lanes and cannot block or silently alter the core validation verdict. |
| FEEDBACK-001 | Post-MVP, retain feedback in the database for later review. A reply to a bot message is contextual feedback about that wording or result; a standalone message is general feedback. Capture, retention, review, and deletion mechanics require a later decision. |
| DAY-001 | Post-MVP W018: offer the combined completion/activity check-in according to the accepted dinner/reminder behavior. It is not an MVP requirement. |
| DAY-002 | Post-MVP W018: support the accepted completion/activity actions and closure semantics. MVP records steps independently and has no close-day action. |
| DAY-003 | Post-MVP W018: late food additions preserve any later-defined day-completeness state without requiring another check-in. MVP food totals update continuously. |
| CALC-001 | The LLM proposes interpretations. The backend owns identity, authorization, reference resolution, calculations, and durable mutations. |
| CALC-002 | Unknown nutrients are not zero. Preserve source quality, units, edible/raw/cooked basis, and available bounds. Do not infer missing fat or carbohydrate solely from total calories. |
| HYBRID-001 | Support hybrid tracking: an honest estimate is preferable to skipping a meal, uncertainty must remain visible, and measurement effort should focus on oils, sauces, dressings, spreads, and other calorie-dense foods. Stable personal portion references may be reused as confidence grows. |
| DATA-001 | Preserve traceability and ordinary correction history under an agreed retention policy. Revisions are not an exemption from account erasure. |
| DATA-002 | Retrying a delivery or an operation must not apply its domain mutation twice. Distinct user messages must not be deduplicated merely because their text matches. |
| DATA-003 | Scope every personal read, mutation, and reference to its authenticated owner, including recipes, sources, revisions, and pending actions. |
| UX-001 | Keep replies useful and nonjudgmental. Do not moralize food, prescribe compensation, or treat exercise as permission to eat. |

Europe/Berlin is the initial configured time zone, not a hard-coded UTC offset. Preserve the date targeted by a message or clarification; detailed resolution and any future scheduled behavior belong in the conversation specification.

## Boundaries and changes

Detailed interaction rules live in [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); implementation structure lives in [architecture-plan.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/architecture-plan.md?type=file&root=%252F). The current validation boundary is recorded in [D049](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0049-mvp-validation-boundary.md?type=file&root=%252F), and the runnable acceptance slice is [W027](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/027-mvp-hypothesis-validation.md?type=file&root=%252F). Open choices and their owners live in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). Do not treat a recommendation or an implemented schema as approval of unresolved product behavior.

The lead assistant maintains this document whenever an authorized change affects product scope or enduring requirements. Record consequential changes in a decision record, update affected specifications and acceptance criteria in the same work, and preserve superseded reasoning. The user should not need to repeat decisions or remind the assistant to update documentation.
