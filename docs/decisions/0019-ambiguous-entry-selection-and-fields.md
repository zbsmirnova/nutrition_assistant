# D019 — Clarify ambiguous entry targets and bounded correction fields

Kind: product/technical
Status: accepted for W010
Recorded: 2026-09-23.
Decision owner: product owner for the numbered interaction; architect for the bounded implementation.

## Decision

When a correction, deletion, or undo description matches more than one current food entry, the bot keeps the operation unresolved and asks the user to choose a numbered candidate. The choices expose only backend-projected metadata such as description, local date, meal, and current state; database IDs and revision IDs remain private. A reply containing one valid selection resumes the original operation and applies it to that entry. No newest-entry guess is allowed, and the old entry remains in totals until a correction is committed.

W010 also supports two same-entry correction fields: `move_date` and `set_meal`. A date move uses the original message's local date/time zone and explicit date evidence, then recalculates both source and destination day summaries. A meal change creates a new revision on the same day. Both use the existing expected-revision guard and preserve entry identity/history.

## Consequences

The parser receives scoped opaque entry tokens and pending selection metadata. The backend owns numbering, target resolution, authorization, revision checks, date interpretation, and writes. Selection answers carry the original operation's pending-action ID and both source update IDs, so retries remain idempotent. Natural-language target search, multi-component edits, and broader date expressions remain future work.

## References

[conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F), and [010-entry-target-selection-and-fields.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/010-entry-target-selection-and-fields.md?type=file&root=%252F).
