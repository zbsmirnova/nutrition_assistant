# D052 — Defer multi-product messages to V2

Kind: product/technical.
Status: accepted for V2.
Recorded: 2026-09-26.
Decision owner: product owner.
Acceptance evidence: explicit instruction to record list-of-products handling
after the MVP.
Related decisions: D049, D051.

## Context

The deployed MVP worker is intentionally bounded to one food action per message
(with one narrow mixed pending path). A typical message such as “завтрак:
яблоко 88 г; пиво 400 г; яйцо 60 г” is currently classified as unsupported
instead of being partially or unpredictably saved. The live pilot confirmed
that this is a product-scope limitation rather than a transport failure.

## Decision

Keep arbitrary lists of independent food products out of the MVP release gate.
For the MVP pilot, the reliable input form is one food item per Telegram
message. A list message must not silently save an arbitrary subset or claim that
the whole list was recorded.

Add list processing as a V2 slice. That slice must define bounded handling for
multiple independent actions, per-item resolution and clarification, stable
operation identities, partial-success semantics, and one clear user-facing
response. It must preserve the existing exactly-once and correction guarantees.

When a V2 clarification asks for a product or recipe weight, the user may
answer through any of three Telegram forms: reply to the original food
message, reply to the bot's clarification message, or a new standalone
message. A standalone answer may use natural Russian wording such as `там
было граммов 200`, `примерно 200 грамм`, or equivalent forms, including
ordinary punctuation and spacing variants. The backend must attach the answer
to the correct pending context, preserve the user's exact-versus-approximate
meaning, and ask for disambiguation when more than one pending quantity could
match; it must not guess from an unrelated standalone number.

## Consequences

The MVP remains suitable for validating single-item calculation and durable
recording, but it does not yet match the user's fastest breakfast-entry format.
The V2 design should be completed before changing the worker's current
unsupported disposition for multi-action proposals. The three clarification
entry points and free-form weight wording belong to that V2 design and do not
change the MVP's current one-message, reply-linked clarification behavior.

## References

[CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F),
[roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F),
[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F),
and [W027 live E2E notes](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/027-live-e2e-notes.md?type=file&root=%252F).
