# D031 — Exclude scheduled check-in reminders from MVP

Kind: Product.
Status: accepted for MVP; supersedes the scheduled-fallback portion of D030.
Recorded: 2026-09-23.
Decision owner: product owner.
Acceptance evidence: the user instructed the assistant to exclude scheduled reminders from MVP.
Related decisions: D001, D030.

## Decision

The MVP offers the combined completion/activity check-in only when a successfully logged dinner is acknowledged. It does not send a 21:00 fallback or any other scheduled completion reminder. If no dinner is logged, no automatic check-in is created for that day.

The dinner-triggered offer keeps D030's three actions: “Everything logged”, “Add steps”, and “Later”. Closure and completion suppress the offer; late food additions do not create another offer. The user may still send a conversational close command without waiting for a reminder.

Scheduled reminder rules, local-time scheduling, DST occurrence handling, notification runs, and scheduled-outbox delivery are outside MVP and are planned as [W019](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/019-scheduled-check-in-reminders.md?type=file&root=%252F). Weekly reports remain a separate open question.

## Consequences

W018 no longer needs a scheduler, fallback occurrence keys, DST scheduler tests, notification rules, or notification-run rows. Its MVP runtime needs dinner-triggered check-in persistence, inline-keyboard/callback transport, stale-callback validation, and idempotent use of the existing ordinary reply outbox. W019 is the planned post-MVP reminder slice and must settle those deferred mechanics before coding.

D030 remains historical for the dinner-triggered behavior and its action semantics; its 21:00 fallback is superseded for MVP. A later reminder feature must introduce a new technical decision before implementation.

## References

[D030](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0030-combined-check-in-behavior.md?type=file&root=%252F), [W018](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F), [DAY-001 in the constitution](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F).
