# D024 — Offer numbered recipe choices and an exact-name fallback

Kind: product
Status: accepted for W014
Recorded: 2026-09-23.
Decision owner: product owner, selected in the project discussion.

## Decision

When a consumed-food message matches more than one saved recipe, keep the food action pending and ask one clarification that offers both paths: show numbered candidates and accept either a number or a more specific recipe name. Candidate choices should use the existing opaque references and concise recipe details; the user's reply must resolve exactly one current owned recipe before a food command is created.

If eaten grams are missing or expressed as a serving, the same clarification flow asks for explicit grams. A clarification answer resumes the original message and operation, preserves its date/evidence, and does not duplicate any already committed independent action.

## Consequences

W013 remains the bounded resolver for explicit refs and unique names. W014 adds pending recipe candidates, selection/text/gram answers, safe resumption, and user-facing clarification rendering. No generic product substitution, default portion, or recipe batch is introduced.

## References

[013-conversational-recipe-resolution.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/013-conversational-recipe-resolution.md?type=file&root=%252F), [014-recipe-clarification.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/014-recipe-clarification.md?type=file&root=%252F), and [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F).
