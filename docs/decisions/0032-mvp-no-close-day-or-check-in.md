# D032 — Defer close-day and check-in behavior from MVP

Kind: Product.
Status: accepted for MVP; supersedes the MVP scope of D030 and D031.
Recorded: 2026-09-23.
Decision owner: product owner.
Acceptance evidence: the user decided that continuous meal persistence removes the need for close-day and asked to move the triggering reminder together with scheduled reminders into W018 after MVP.
Related decisions: D001, D030, D031.

## Decision

The MVP does not include a “close day” command, a dinner-triggered completion check-in, completion buttons, or scheduled completion reminders. Food is persisted continuously as each meal is processed. Steps are recorded independently through the W017 observation flow.

The combined check-in remains a post-MVP feature. W018 will own the complete future flow: a dinner-triggered offer together with the optional scheduled reminder, shared daily-offer identity, activity action, closure semantics, and Telegram interaction. The separate W019 reminder brief is merged into W018's post-MVP scope.

## Consequences

There is no MVP food-completeness confirmation, completion state transition, or requirement to wait for a close-day action before reporting saved food. Late food naturally updates the persisted entries and totals. Missing steps remain an independent observation concern.

DAY-001–DAY-003, D030's dinner trigger, D031's reminder exclusion, and their callback/scheduler mechanics remain historical or deferred requirements. W018 must be rewritten as planned post-MVP work before implementation; no callback or scheduler transport is needed for the MVP.

Weekly reports remain a separate product decision.

## References

[W017](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/017-daily-observations.md?type=file&root=%252F), [W018](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F), [W019](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/019-scheduled-check-in-reminders.md?type=file&root=%252F), [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F).
