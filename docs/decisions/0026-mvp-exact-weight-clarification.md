# D026 — Ask for exact weight or an explicit assumption in the MVP

Kind: product.
Status: accepted.
Recorded: 2026-09-23.
Decision owner: product owner.
Acceptance evidence: the user stated, “for the first glance (MVP) lets always ask user about the exact weight or their assumption”.
Related questions: Q04, Q09.

## Context

The live diagnostic sample extracted candidates and quantities correctly, but it missed required clarification for approximate cafeteria food and bone-in chicken. Restaurant portions, bones, edible portions, ranges, and partial servings can make a numerically valid quantity unsuitable for nutrition calculation. FOOD-002 already requires clarification of material missing details and explicit approval for estimates.

## Decision

For the MVP, do not silently accept a food amount whenever the usable amount is not an exact, compatible quantity. Ask the user to provide the exact usable weight or explicitly approve an assumption.

This applies to approximate amounts, ranges or bounds, partial portions, counts without a trusted mass conversion, bone/skin or other inedible-weight ambiguity, gross-versus-edible ambiguity, and cooked-yield uncertainty. An exact compatible gram or millilitre amount with a clear raw/cooked/as-sold basis does not trigger this question.

The pending action remains outside totals until the user answers. A precise answer resumes the original action. An explicitly approved assumption may proceed only when the response records that it is an assumption and keeps the resulting nutrition visibly estimated; it must never be presented as an exact measured weight. The implementation must preserve the approval and assumption in the frozen source/provenance chain before claiming this path is complete.

Ask the material weight question together with other known blocking details when that reduces friction. Do not ask for exact weight solely to classify a meal or when the message already supplies an exact compatible amount.

## Consequences

This favors safe deferral and transparent estimates over silent false precision. It adds clarification turns for restaurant and mixed-food messages, but it does not require another model call: the backend can detect known ambiguity markers and keep the action pending. The policy applies even when the model returns a complete-looking action; backend resolution remains authoritative.

The current parser and food-component command types do not yet carry a dedicated assumption marker. Until that provenance is implemented, the backend must keep assumption-based amounts pending rather than silently treating them as measured.

## References and replacement history

Updates [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), the Q04/Q09 register, and the delivery roadmap. No previous decision is superseded; this narrows the MVP clarification behavior under FOOD-002 and CALC-002.
