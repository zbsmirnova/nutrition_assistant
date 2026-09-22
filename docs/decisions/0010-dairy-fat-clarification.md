# D010 — Clarify material dairy fat percentage

Kind: product.
Status: accepted.
Recorded: 2026-09-22.
Decision owner: product owner; lead assistant maintains the specification.
Acceptance evidence: the user asked to clarify fat percentage for творог and other dairy products because it affects the nutrition result.
Related requirements: FOOD-002, FOOD-004, CALC-001/CALC-002.

## Context and decision

The earlier W003 example, “Съела 100 г творога”, omitted a material product detail. Treat that as an unresolved dairy entry unless the supplied context already identifies its exact product/profile. Ask for the missing fat percentage before assigning a nutrition source.

Apply the existing rules consistently: reuse facts from the message or an exact identified product/label, retain the original quantity/date while pending, save independent clear items, and resume the original operation once. A percentage is not an eaten quantity. Neither a single catalog candidate nor the most recently used variant establishes the user's intended fat percentage.

The detailed interaction and examples belong in the conversation specification. Fat percentage does not supply a complete nutrition profile; backend calculations continue to use a matched source with explicit unknowns. Do not silently manufacture calories/macros or use an average substitute.

## Consequences and implementation boundary

The W003 successful-add example now specifies a fat percentage and a uniquely identified synthetic product. Its resolver must defer missing or conflicting dairy variants. Sending the question and consuming its answer remain part of the subsequent clarification workflow; this decision does not claim that workflow is implemented.

Record this as a refinement of FOOD-002, not an open product question. Preserve the current contract and database versions until the resolver implementation establishes any required representation changes. No new runtime behavior or live-model validation is implied by this specification change.

## References and replacement history

- [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F) owns the interaction rules.
- [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F) owns resolver acceptance criteria.
- [scenarios-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/scenarios-v1.md?type=file&root=%252F) adds specified scenarios S28–S31; execution remains not run.

This refines missing-detail handling without superseding continuous saving, partial logging, or explicit estimate approval.
