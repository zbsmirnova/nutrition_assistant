# D047 — MVP nutrition uncertainty ranges and restaurant portion requirement

Kind: product/technical.
Status: accepted for the estimate experiment; not part of the core MVP validation gate.
Recorded: 2026-09-25.
Decision owner: product owner.
Acceptance evidence: explicit user acceptance of the ±25% restaurant coefficient and the range-based display policy.
Related questions: Q04.

## Context

The estimate experiment prioritizes useful trend tracking over laboratory
precision. Every food estimate is approximate, but displaying that word on
every line would add noise. A numeric range provides a consistent
representation of uncertainty while keeping the Telegram reply short.

The subsequent MVP validation decision ([D049](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0049-mvp-validation-boundary.md?type=file&root=%252F)) separates this estimate experiment from the core release gate. The range arithmetic remains valid for known personal products and recipes; unknown-food and restaurant model quality is measured separately.

## Decision

The backend stores a central estimate and lower/upper bounds for kcal, protein,
fat, and carbohydrates.

- Ordinary food uses a working uncertainty coefficient of ±10%.
- Restaurant food uses a working uncertainty coefficient of ±25%.
- Restaurant food cannot be recorded without a user-supplied exact weight or
  weight range, such as `150–200 г`.
- A user-supplied weight range expands the nutrition range separately.
- For a per-100-g central estimate `n`, coefficient `r`, and weight range
  `[w_min, w_max]`, bounds are `n * (1 - r) * w_min / 100` and
  `n * (1 + r) * w_max / 100`.
- Daily bounds are sums of the included entry bounds; pending food is excluded.
- A single food reply shows central kcal and protein. The daily reply shows
  kcal and protein ranges. Fat and carbohydrate values and bounds are retained
  in the database but omitted from routine MVP Telegram copy.

The personal product and recipe database remains the first source for known
items. For an unknown product or restaurant dish, the LLM supplies the central
nutrition estimate. The backend validates obvious malformed or impossible
values, applies the coefficient and weight arithmetic, and persists the
source message, model identity, prompt version, estimate, and bounds. It does
not use an open food database to choose a restaurant estimate in this experiment.

## Consequences and limits

The coefficients are operational defaults, not statistical confidence
intervals. They are intentionally simple and will be reviewed against real
corrections during the personal pilot. The policy does not attempt strict
calorie-from-macros reconciliation; it only rejects negative values, invalid
units, and clearly impossible magnitudes.

## References

See [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), and [0043-external-food-catalog-fallback.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0043-external-food-catalog-fallback.md?type=file&root=%252F).
