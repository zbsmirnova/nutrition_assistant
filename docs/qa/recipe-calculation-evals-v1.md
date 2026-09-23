# Recipe calculation evaluation draft v1

Status: authored from user-provided cases; not executed against a live model or recipe runtime.
Owner: product owner supplies behavior; QA/lead assistant maintains the executable representation.

[recipe_calculation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/recipe_calculation_v1.json?type=file&root=%252F) contains the tuna/Frischkäse, red-lentil, and oatmeal calculations. It keeps calculation behavior separate from [recipe_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/recipe_v1.json?type=file&root=%252F), which evaluates recipe recall and ambiguity.

Each case retains original ingredient amounts, provisional yield, calculation output, and uncertainty. A recipe calculation does not log consumption. Generic catalog products can validate that a calculated result is plausible, but cannot replace a recipe-specific calculation. A finished cooked weight supersedes a provisional sum-of-ingredients yield for the recipe's per-100-g profile.
