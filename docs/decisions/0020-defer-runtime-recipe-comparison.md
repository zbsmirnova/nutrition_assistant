# D020 — Defer runtime comparison with a general food database

Kind: product/technical
Status: accepted for recipe persistence
Recorded: 2026-09-23.
Decision owner: product owner.

## Decision

Recipe v1 proceeds with backend-owned deterministic ingredient arithmetic and per-100-g nutrition. It does not query or claim validation against an external general food database at runtime until a data provider, licensing/data-sharing policy, and matching behavior are selected.

The existing oatmeal/USDA comparison remains an offline evaluation reference for the calculation foundation. It is evidence about the arithmetic fixture, not a live provider integration or a requirement to accept a model-suggested substitute.

## Consequences

Recipe responses may state the calculated result and its yield basis. If no local source is available for an ingredient, the recipe remains unresolved or retains an honest unknown nutrient; the system does not invent a close product. A future comparison provider must be introduced through a separate decision and work brief.

## References

[005-recipe-calculation.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/005-recipe-calculation.md?type=file&root=%252F), [0014-recipe-yield-policy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0014-recipe-yield-policy.md?type=file&root=%252F), and [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F).
