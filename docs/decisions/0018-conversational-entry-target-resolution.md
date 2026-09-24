# D018 — Resolve bounded conversational food-entry targets

Kind: technical
Status: accepted for W009
Recorded: 2026-09-23.
Decision owner: architect under FOOD-003, DATA-002, and the accepted correction target rules.
Acceptance evidence: the conversation contract already specifies reply-first, explicit-reference, and ambiguity behavior. This record defines the first executable subset.

## Decision

W009 resolves correction, delete, and undo proposals against a backend-owned current-entry context:

- A reply target resolves only when the replied-to Telegram message is the source of a committed food operation owned by the actor.
- An entry candidate resolves through an opaque scoped token supplied in the parser context. The parser never receives database IDs.
- A described target resolves only when exactly one current entry has that description. Multiple matches remain unresolved; the resolver never chooses the newest entry merely because it is newest.
- A quantity correction is bounded to one current product component and one exact `g` or `ml` quantity evidenced in the correction text. Other changes remain unresolved or unsupported.
- Delete and undo use the same target rules. Undo restores the immediately preceding active revision selected by the backend; if no such revision exists, it remains unresolved.
- Forwarded messages, replies without a matching committed entry, deleted targets for correction/delete, and ambiguous descriptions remain outside totals and create no prepared command.

Implementation guard: when Telegram reply metadata maps to exactly one current entry, but the provider emits a description that matches no current entry (for example, a truncated Russian name), the resolver uses the backend reply target. It does not override a valid explicit description or candidate target, and it does not weaken the unresolved behavior for missing or ambiguous replies.

This slice invokes W008's guarded typed commands. It does not claim live-model accuracy, arbitrary date/meal disambiguation, multi-component corrections, pending corrections, or message-edit support.

## Alternatives and consequences

Letting the model name an entry ID would bypass ownership and revision checks. Choosing the newest matching entry would silently mutate the wrong meal when two servings share a name. A narrow unresolved result is preferable to an unverified correction.

## References

FOOD-003, FOOD-006, DATA-002, DATA-003 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F); and [009-conversational-entry-targets.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/009-conversational-entry-targets.md?type=file&root=%252F).
