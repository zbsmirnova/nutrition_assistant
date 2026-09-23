# Recipe recall evaluation draft v1

Status: authored from user-provided behavior; not executed against a live model or recipe runtime.
Owner: product owner supplies behavior; QA/lead assistant maintains the executable representation.

[recipe_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/recipe_v1.json?type=file&root=%252F) begins the recipe suite with normalized user-scoped recall. `RECIPE-001` requires ordinary word-order variants to resolve the same uniquely matching recipe; `RECIPE-002` requires clarification when normalized names are ambiguous. Both prohibit generic catalog fallback and cross-user lookup.

This suite is intentionally separate from food-intake calculation. Recipe creation, ingredient calculation, instructions, version updates, and consumption of a saved recipe need their own cases as those M3 behaviors are specified and implemented.
