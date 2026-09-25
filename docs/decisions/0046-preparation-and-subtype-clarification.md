# D046 — Clarify preparation and subtype when nutrition materially differs

Kind: product.
Status: accepted for MVP conversation behavior.
Recorded: 2026-09-24.
Decision owner: product owner.
Acceptance evidence: explicit user acceptance of the proposed clarification examples.
Related questions: Q04.

## Context

The source comparison for common foods showed that a robust average is useful
only inside a homogeneous group. “Baked chicken”, “omelette”, “42% cheese”,
and “baked potato” can represent materially different nutrition profiles
depending on skin, added fat, cheese subtype, variety, or preparation. Mixing
these groups creates a systematic error that a 7% tolerance cannot remove.

## Decision

In the MVP, when the message does not resolve a nutrition-relevant preparation
or subtype, ask one concise clarification before recording the affected food.
The accepted examples are:

- “Куриная грудка: без кожи и масла?”
- “Яичница: сколько масла или сливочного масла добавлено?”
- “Сыр 42%: какой сорт или производитель?”
- “Картошка: с маслом или без?”

The answer becomes part of the food identity and source basis. Until it is
answered, the affected action remains pending and outside totals. A previously
confirmed exact product or preparation may be reused without another question.

This decision does not require a fixed number of external sources or authorize
the model to select an average. If an average is introduced later, the backend
must deduplicate sources, group compatible preparation/subtype records, and
retain the source set and calculation method.

## Consequences and limits

The rule adds a clarification turn for ambiguous foods but avoids silently
combining incompatible nutrition profiles. It applies to nutrition-affecting
distinctions, not to meal labels or harmless wording differences. Exact source
selection, robust-average thresholds, and uncertainty display remain a later
technical/product design task.

## References

See [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), and [user-guide-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/user-guide-v1.md?type=file&root=%252F).
