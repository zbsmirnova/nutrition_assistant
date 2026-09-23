# D025 — Normalize explicit quantity ratios into component weights

Kind: Product/technical  
Status: accepted for interpretation and intake evaluation  
Recorded: 2026-09-23.  
Decision owner: product owner, clarified in the project discussion.

## Decision

When a consumed-food message gives named components, an explicit ratio, and a total mass, the proposal must represent the component masses after applying that ratio. For example, “яйцо + белок 1:1, 115 гр” means 57.5 g of egg and 57.5 g of egg white.

The split is valid only when the ratio and total are explicit and the arithmetic is determinate. The backend remains authoritative: it recalculates and validates the component masses, their sum, units, and source basis before creating a trusted command. The model must not distribute a quantity when the ratio is absent, approximate, ranged, or otherwise ambiguous.

## Consequences

Interpretation evaluation cases score the component quantities (`57.5`, `57.5`) rather than the unsplit total for this pattern. The parser prompt must preserve the ratio evidence and select the supplied component candidates. The existing numeric intake fixture already uses this normalization. Multi-action command execution and any durable representation of the ratio dependency remain implementation work; this decision does not authorize model-supplied nutrition or arithmetic without backend validation.

## References

[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), [interpretation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/interpretation_v1.json?type=file&root=%252F), and [food_intake_calculation_v1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/evals/food_intake_calculation_v1.json?type=file&root=%252F).
