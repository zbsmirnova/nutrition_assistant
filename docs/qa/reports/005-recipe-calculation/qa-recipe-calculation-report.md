# Recipe calculation QA report

Date: 2026-09-23  
Scope: conditional ingredient-sum yield and deterministic per-100-g recipe arithmetic  
Fixture: `recipe.oatmeal_sum_yield.v1`

The oatmeal calculation passes the requested behavior. The selected catalog snapshot yields 357.68 kcal for 470 g, displayed as approximately 358 kcal and 76 kcal/100 g. Ingredient sums retain full Decimal precision until final output; bounded nutrients preserve their bounds, and unknown nutrients stay unknown.

The command schema accepts `ingredient_sum_no_evaporation` without an approval update. `user_confirmed_estimate` still requires an evidence-linked approval. Volume normalization remains outside the calculator and requires a pinned density; the fixture explicitly normalizes 375 ml water at 1 g/ml.

The retained USDA FoodData Central responses were fetched on 2026-09-23 from the public API with `DEMO_KEY`: dry oats FDC 173904 (379 kcal/100 g), granulated sugar FDC 169655 (387 kcal/100 g), and prepared oatmeal FDC 173905 (71 kcal/100 g). The dry-reference calculation is 360.21 kcal, within 3 kcal of the selected catalog snapshot. The prepared item is a comparison only; it has a different hydration/product formulation. Evaporation alone would increase kcal/100 g by lowering yield.

Developer verification: 94 offline tests passed, including the contract, arithmetic, USDA comparison fixture and generated-schema drift checks. No recipe migration, provider call, or personal data was used. Independent review focused on arithmetic, schema and the fixture's supplied reference values; it did not independently fetch the primary USDA records. The precision and evaporation-direction findings were corrected before closeout.

Evidence:

- [recipe_oatmeal_sum_yield_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/fixtures/recipe_oatmeal_sum_yield_v1.json?type=file&root=%252F)
- [offline-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-recipe-calculation/offline-output.txt?type=file&root=%252F)
- [usda-oats-173904.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-recipe-calculation/usda-oats-173904.json?type=file&root=%252F)
- [usda-sugar-169655.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-recipe-calculation/usda-sugar-169655.json?type=file&root=%252F)
- [usda-prepared-oatmeal-173905.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/005-recipe-calculation/usda-prepared-oatmeal-173905.json?type=file&root=%252F)
