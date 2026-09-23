# D031 — Exclude scheduled check-in reminders from MVP

Kind: Product.
Status: historical; MVP scope superseded by D032.
Recorded: 2026-09-23.
Decision owner: product owner.
Acceptance evidence: the user instructed the assistant to exclude scheduled reminders from MVP.
Related decisions: D001, D030.

## Decision

The MVP offers no combined completion/activity check-in and no scheduled completion reminder. This decision was superseded by D032, which also defers the dinner-triggered offer itself.

The post-MVP check-in proposal retained D030's three actions: “Everything logged”, “Add steps”, and “Later”. That proposal is now owned by post-MVP W018.

Scheduled reminder rules, local-time scheduling, DST occurrence handling, notification runs, and scheduled-outbox delivery are outside MVP and remain part of post-MVP W018. Weekly reports remain a separate open question.

## Consequences

W018 was previously narrowed to a dinner-triggered MVP flow. D032 supersedes that scope: no check-in transport or scheduler is needed before MVP. The future W018 slice must settle callback, scheduler, DST, and scheduled-outbox mechanics together.

D030 remains historical for the dinner-triggered behavior and its action semantics; its 21:00 fallback is superseded for MVP. A later reminder feature must introduce a new technical decision before implementation.

## References

[D030](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0030-combined-check-in-behavior.md?type=file&root=%252F), [W018](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F), [DAY-001 in the constitution](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F).
