# D022 — Pin recipe versions when food is consumed

Kind: product/technical
Status: accepted for W012
Recorded: 2026-09-23.
Decision owner: architect under the accepted recipe model.

## Decision

A consumed recipe component stores the exact `recipe_version_id` selected at the time of logging and the grams eaten. The backend scales that immutable version's per-100-g nutrition and persists the resulting snapshot in the food-entry revision. Later recipe revisions affect only future selections; they never rewrite historical meals.

Food components explicitly distinguish product and recipe sources. Recipe components have no product source or product weight basis; they use mass grams and the recipe calculation version. Recipe consumption remains a normal food-entry mutation, so it shares idempotent operation identity, revision history, daily totals, and outbox behavior.

## Consequences

Natural-language recipe lookup and clarification must resolve one owned current recipe version before producing `RecipeComponent`. A recipe's stored serving size or cooked batch is never introduced. Existing product-food correction and resolver paths remain bounded until recipe-aware corrections are added.

## References

[011-recipe-persistence.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/011-recipe-persistence.md?type=file&root=%252F), [012-recipe-consumption.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/012-recipe-consumption.md?type=file&root=%252F), and [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F).
