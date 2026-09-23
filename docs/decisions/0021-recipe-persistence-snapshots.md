# D021 — Persist immutable recipe versions and ingredient snapshots

Kind: technical
Status: accepted for W011
Recorded: 2026-09-23.
Decision owner: architect under the accepted recipe model and D014/D020.

## Decision

Recipes use a stable `recipes` identity with an immutable `recipe_versions` history and immutable `recipe_ingredients` snapshots. A version stores the user-facing name, optional instructions, per-100-g nutrition, and calculation provenance. Original ingredient quantities and source-resolution details are retained as typed JSON snapshots so later edits cannot rewrite earlier recipes.

The backend calculates calculated profiles from pinned product versions and normalized mass quantities. A volume ingredient is accepted only when the command already supplies a normalized mass; the service does not invent density conversions. Provided per-100-g profiles are checked against an owned data-source row. Runtime comparison with a general database is deferred by D020.

## Consequences

Define and revise operations are idempotent through the existing prepared/applied operation path. Revisions require the current version ID and never change earlier versions. Recipe retrieval returns the current version with original ingredient details. Recipe consumption and conversational recipe resolution remain later slices.

## References

[005-recipe-calculation.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/005-recipe-calculation.md?type=file&root=%252F), [0020-defer-runtime-recipe-comparison.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0020-defer-runtime-recipe-comparison.md?type=file&root=%252F), and [011-recipe-persistence.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/011-recipe-persistence.md?type=file&root=%252F).
