# D027 — User decisions control MVP assumptions

Kind: product.
Status: accepted.
Recorded: 2026-09-23.
Decision owner: product owner.
Acceptance evidence: the user stated, “also lets keep MVP more user desicions driven then model approximations”.
Related decisions: D026, D020, D025.

## Context

The diagnostic model handled candidates and quantities well, but clarification recall for materially uncertain restaurant weights was low. Nutrition estimates can also arise from edible-weight assumptions, unknown recipes, average products, or incomplete portions. The MVP must keep the user in control of those choices.

## Decision

The model may identify ambiguity, enumerate bounded options, and ask a clarification. It may not autonomously choose an approximation, average, serving conversion, edible-weight assumption, recipe substitute, or other nutrition-affecting interpretation that the user has not explicitly approved.

The backend remains authoritative for arithmetic, identity, dates, provenance, and writes. A user decision must be explicit in the message or a typed clarification answer, and the resulting entry must remain visibly marked as assumed or estimated. If the user has not made that decision, keep the action pending and exclude it from totals.

For MVP behavior, prefer a concise clarification with the known alternatives over silent model completion. Do not require another model call; the backend can hold the action and render the question.

## Consequences

This adds clarification turns and may lower automatic logging coverage, but it prevents hidden model choices from becoming personal nutrition history. It is especially important for restaurant dishes, shared portions, bones/skin, uncertain cooked yield, unknown recipes, and catalog gaps.

The assumption marker and approval provenance still need implementation. Until they exist in the command/persistence path, an assumption answer remains pending rather than being stored as an exact amount.

## References and replacement history

D027 strengthens D026’s exact-weight policy and applies the same user-authority rule to all MVP nutrition-affecting approximations. It updates [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), the decision register, and the roadmap.
