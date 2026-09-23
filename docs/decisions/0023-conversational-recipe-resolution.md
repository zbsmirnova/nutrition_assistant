# D023 — Resolve saved recipes through scoped opaque candidates

Kind: technical
Status: accepted for W013
Recorded: 2026-09-23.
Decision owner: architect under the accepted recipe model.

## Decision

The conversation worker supplies the parser with the user's current recipe names as opaque `c` references. The request projection contains only each reference and name; recipe and version database identifiers remain backend-only. A parser proposal may select a recipe reference or provide a recipe name. The backend resolves the reference to the user-owned current recipe version and creates the existing `RecipeComponent` command with explicit eaten grams.

A named recipe is auto-selected only when exactly one current owned recipe matches. Missing or duplicate matches remain unresolved and do not create food. An explicit recipe candidate reference is sufficient to select one scoped recipe, even when names are duplicated. No serving default, cooked batch, generic product substitution, or model-supplied nutrition is introduced.

## Consequences

Recipe consumption now shares the product resolver's date, quantity, evidence, operation, retry, and daily-total behavior. Recipe-name aliases, broader inflection-aware retrieval, recipe-aware corrections, and multi-action recipe definition plus consumption remain later work. W014 adds the accepted bounded clarification path. The parser context is bounded by the combined product/recipe candidate limit.

## References

[013-conversational-recipe-resolution.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/013-conversational-recipe-resolution.md?type=file&root=%252F), [012-recipe-consumption.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/012-recipe-consumption.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), and [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F).
