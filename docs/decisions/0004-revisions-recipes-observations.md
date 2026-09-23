# D004 — Corrections, recipe data, and daily observations

Kind: product.
Status: accepted.
Recorded: 2026-09-22.
Decision owner: product owner.
Acceptance evidence: the discussion explicitly accepted food revision history, pending clarifications outside totals, one weight and one steps value per day, late-addition completeness, and subsequent conversation/recipe clarifications. No separate timestamp is asserted for each earlier message.

## Decision

- Correct the same food entry with retained history. An unresolved correction leaves the committed entry unchanged until resolved.
- Save independent clear items in a mixed message; keep unresolved items pending and outside totals. A later answer applies only the unresolved operation.
- Store recipe kcal and macronutrients per 100 g. Preserve original ingredient amounts/units and supplied cooking instructions for repeat cooking, as clarified later in the discussion.
- Accept arbitrary recipe ingredient amounts and ask for material missing calculation inputs. No default portion, serving count, or separate cooked-batch entity is needed. Eaten grams belong on consumed-food entries.
- Recall recipes within the authenticated user's recipes by normalized ordinary wording, including word-order variants. Select only a unique match; missing or ambiguous recall requires a clarification and never falls back to a generic product.
- Keep one current body weight and one current steps total per user/local date, with history for replacements.
- Normal food replies show the saved/corrected entry and updated daily nutrition totals with honest coverage.

## Alternatives and consequences

Multiple current daily weight readings and averaging are not the requested model. Recipe batches and stored default portions would add a lifecycle the user declined. Corrections must not masquerade as extra consumption.

Recipe calculations can require a usable finished edible yield; any retained calculation yield is provenance, not a default serving or preparation entity. Exact provenance columns and physical revision storage remain technical proposals. Versioned recipe/product sources preserve earlier meal values as required by the brief and current specifications.

This record supersedes earlier recipe batch/portion and multiple-weight proposals. It also incorporates the later clarification to retain original recipe ingredients/instructions; “per 100 g” is the nutrition basis, not a reason to discard the cooking definition.

## References

FOOD-002–FOOD-006, RECIPE-001–RECIPE-003, OBS-001/OBS-002 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F). Late-addition completion is recorded in D001.
