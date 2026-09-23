# Food-intake calculation evaluation draft v1

Status: authored from user-provided real-life cases; synthetic fixture values are frozen, live execution is pending.
Owner: product owner supplies behavior; QA/lead assistant maintains the executable representation.

[food_intake_calculation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/food_intake_calculation_v1.json?type=file&root=%252F) records the nine agreed intake cases. A case is a reproducible episode: user turns, explicit fixture requirements, expected interpretation/resolution/persistence/calculation behavior, and prohibited behavior.

## How this set is scored

Score three layers separately. The interpreter must extract the intended food, quantity, user reference, preparation detail, or needed clarification. The application must resolve only the required user-scoped recipe/product/history source. The deterministic nutrition engine must calculate using the source/version selected by the application and preserve unknowns and estimates.

The shared synthetic sources are frozen in [food_intake_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/fixtures/food_intake_v1.json?type=file&root=%252F): per-100-g nutrition, recipe/profile versions, the standard physalis weight, history state, grouping window, and the bone-answer continuation. Resolvable cases now declare exact six-decimal component and day totals. Cases awaiting sauce, bones, or recipe confirmation declare only a known subtotal or a continuation result; they never invent a final meal total.

## Current limits

These nine cases are sufficient to validate the annotation format and start a food-intake regression suite. They are not enough to select a live model or establish end-to-end quality. Add separate cases for plans versus consumption, corrections/undo, recipe version updates, labels and partial macros, ambiguous references, date/history boundaries, daily totals and closure idempotency, observations, persistence failures, and multi-turn clarification answers. Keep later development examples separate from a held-out model-selection set.
