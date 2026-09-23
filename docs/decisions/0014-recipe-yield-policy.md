# D014 — Conditional recipe yield from ingredient mass

Kind: product/technical.
Status: accepted for the oatmeal recipe slice.
Recorded: 2026-09-23.
Decision owner: lead architect/developer under the user's concrete recipe example.

## Decision

Recipe nutrition is calculated from each resolved ingredient's per-100-g nutrition and normalized edible mass. When every ingredient has an unambiguous mass equivalent and the source does not provide a measured cooked yield, the backend may use the sum of those masses with the yield basis `ingredient_sum_no_evaporation`.

This basis is explicitly conditional: it does not claim that water evaporation, draining, or cooking loss was measured. The saved recipe keeps the ingredient amounts and the yield basis as provenance; it does not create a default portion or serving size. Recipes whose cooking process makes the sum unreliable should still ask for a measured yield or an explicitly approved estimate.

For the oatmeal case:

- 93 g oats + approximately 2 g sugar + 375 ml water normalized at 1 g/ml = approximately 470 g.
- Using the selected general-catalog snapshot (376 kcal/100 g oats and 400 kcal/100 g sugar) gives 357.68 kcal total, displayed as about 358 kcal.
- The conditional density is 76.102128 kcal/100 g, displayed as 76 kcal/100 g.

## Validation

USDA FoodData Central close references produce 360.21 kcal for the same dry-ingredient quantities (379 kcal/100 g dry oats, 387 kcal/100 g granulated sugar), within 3 kcal of the selected snapshot. USDA's prepared oatmeal-with-water item is 71 kcal/100 g; that comparison uses a different hydration ratio and product formulation. Evaporation by itself would reduce yield and increase kcal/100 g, so the conditional result must not claim that evaporation explains the lower reference. The IDs and source links are retained in `evals/fixtures/recipe_oatmeal_sum_yield_v1.json`.

## Consequences

The trusted command schema now distinguishes measured, ingredient-sum conditional, and user-confirmed estimated yields. Arithmetic remains backend-owned, keeps full Decimal precision through component summation, and preserves unknown nutrients. Volume ingredients must be normalized with a pinned source density before they participate in a mass sum; the calculator does not assume that every millilitre equals one gram.

Related: [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), D004 and D006.
