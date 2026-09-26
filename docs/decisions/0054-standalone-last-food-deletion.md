# D054 — Standalone deletion targets the latest active food entry

Kind: Product/technical.
Status: accepted for MVP conversation behavior.
Recorded: 2026-09-26.
Decision owner: product owner.
Related decisions: D017, D018, D019.

## Decision

The user may delete a food entry in three ways:

- by replying to their original food message;
- by replying to the bot's acknowledgment for that saved food;
- by sending a new standalone deletion message.

An explicit standalone deletion without a target, such as `Удали последнюю
запись`, `Удали последнее` or `Удали`, targets the latest active food entry for
that owner in the current conversation scope. “Latest” means the most recently
committed active food entry by backend creation order, not the latest bot
message, clarification, summary, or correction text. The backend resolves this
target and applies the normal expected-revision deletion command.

If the standalone message names a food or date, the named scope must still
resolve to one entry. If it matches several entries, ask the user to choose;
the latest-entry rule applies only to a targetless standalone deletion. If no
active food entry exists, acknowledge that there is nothing to delete and leave
totals unchanged.

All three forms preserve the deleted entry and its prior revisions in history,
remove it from current totals, and are idempotent on replay. A deletion of a
pending clarification does not delete an already saved unrelated entry.

## Consequence

This is a deliberate exception to D019's no-newest-guess rule for ambiguous
correction, deletion, and undo descriptions. It applies only to an explicit,
targetless standalone delete command. Corrections, undo, and named ambiguous
deletions still require an explicit target or numbered selection.

## References

[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F),
[mvp-test-cases-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/mvp-test-cases-v1.md?type=file&root=%252F),
and [D019](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0019-ambiguous-entry-selection-and-fields.md?type=file&root=%252F).
