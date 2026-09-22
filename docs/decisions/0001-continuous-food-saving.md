# D001 — Continuous food saving and optional completion

Kind: product.
Status: accepted.
Recorded: 2026-09-22.
Decision owner: product owner.
Acceptance evidence: the product discussion accepted the optional combined check-in after dinner or at 21:00, and explicitly accepted keeping a day complete after late food additions. Recording date is not a claim about the timestamp of each earlier message.

## Context

The source brief connected final persistence/history to “close the day.” That couples reliable storage to a user remembering an extra command, even though food messages can be validated throughout the day.

## Decision

Save clear consumed-food entries immediately. Keep persistence, logging completeness, nutrition coverage, and missing activity separate.

Recognize conversational closure and the optional “Everything logged” button as the same food-completeness action. The combined check-in offers “Everything logged”, “Add steps”, and “Later” after dinner, or at 21:00 local time if dinner has not been recorded. Suppress the completion action after conversational closure. One logical daily offer covers both triggers, including dinner after the fallback.

Missing steps do not block food completion. A closure acknowledgment can offer missing activity alone. Late food additions update totals and keep the date complete without another closure or check-in.

## Alternatives and consequences

- Save only on closure: rejected in favor of continuous persistence and recoverable partial-day history.
- Automatically confirm at midnight: does not establish that all consumed food was logged.
- Reopen after late additions: not selected by the user; completeness remains confirmed.

Reports must distinguish recorded data from confirmed completeness. Delivery state is separate from day completeness. Dinner recognition, dismissal/expiry, pending-food closure, and empty-day edge cases remain proposed details tracked as Q05/Q06.

## References

Requirements FOOD-001 and DAY-001–DAY-003 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); detailed behavior in [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F); open details in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F). This supersedes the source brief's save-on-close semantics and 21:30 fallback, not its historical provenance.
