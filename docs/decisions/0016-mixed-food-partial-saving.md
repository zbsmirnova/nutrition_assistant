# D016 — Partial saving for one mixed food message

Kind: technical/product
Status: accepted
Recorded: 2026-09-23.
Decision owner: architect under the accepted FOOD-004 behavior.
Acceptance evidence: the user accepted continuous food saving and the conversation contract requires clear independent items to be saved while unclear items remain pending.
Related questions: Q04.

## Context

The parser contract already permits multiple independent actions, while the W003 worker intentionally rejected every multi-action proposal. FOOD-004 requires a clear item to be saved without waiting for an unrelated unclear item, and the later answer must not replay the clear item. The M1 operation identity was originally position zero only.

## Decision

Implement a bounded partial-saving path for exactly two independent `add_food` actions when one resolves to a trusted product command and the other is an unresolved dairy-fat action:

- Resolve each action against its literal evidence excerpt, so quantities from one item cannot make another item appear complete.
- Save the clear command at operation position 0 and retain the unresolved proposal/question at its action position.
- Keep the source conversation job unresolved after the clear command is applied. Its pending count includes only the unresolved item.
- A reply to the original Telegram message resumes the stored pending action at its original operation position, using the original evidence plus the reply. The already applied operation is never reinterpreted or re-created.
- Derive operation IDs from `(origin_update_id, action_position)` for positions 0–31. Existing position-zero IDs remain unchanged.

This slice does not claim general multi-action execution, recipe-plus-food dependencies, multiple pending items, or mixed corrections. Those require a normalized pending-action graph and further atomicity decisions.

## Alternatives and consequences

- Rejecting the whole message is simpler but violates FOOD-004 and delays clear intake.
- Applying all actions in one command would make the unresolved item enter totals and would not provide independent retry identity.
- A fully generalized action graph is the long-term model; this slice deliberately supports one clear plus one dairy-pending item so operation-position and replay behavior can be verified first.

## References and replacement history

[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F), and [007-mixed-food-partial-saving.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/007-mixed-food-partial-saving.md?type=file&root=%252F). D016 extends D002's operation-position convention for M2; it does not supersede D015's pending-state scope.
