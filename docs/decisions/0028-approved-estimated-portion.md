# D028 — Approved estimated portions stay visibly estimated

Kind: Product/technical.
Status: accepted for W016.
Recorded: 2026-09-23.
Decision owner: product owner; implementation delegated to the architect.
Acceptance evidence: user instructed the assistant to continue with the proposed W016 task.
Related decisions: D026, D027.

## Decision

An explicit estimate approval may resolve the portion amount of an already identified, pinned product or saved recipe. The command and persisted component retain `user_approved_estimate` provenance and the clarification update that approved it. Replies must make the estimate visible.

An exact quantity answer remains measured. A bare confirmation without a quantity is insufficient. Unknown restaurant nutrition, average product selection, recipe substitution, and model-generated nutrition remain pending; this decision does not authorize a nutrition source for an unknown dish.

## Consequences

The parser gains a typed `approved_estimate` clarification answer. The backend validates the literal amount and an explicit approval marker, while the command validator and PostgreSQL component row require separate approval evidence. Historical revisions copy the provenance unchanged.

This is a portion-provenance slice only. A later decision is required before an estimate can use an external or generic restaurant nutrition source.
