# D030 — Combined completion/activity check-in behavior

Kind: product
Status: historical; MVP scope superseded by D032.
Recorded: 2026-09-23.
Decision owner: product owner (answers to Q06), recorded by the lead assistant.

## Decision

The combined completion/activity check-in behaves as follows:

- Dinner trigger: when a meal is recognized as dinner, the check-in is offered on the dinner food acknowledgment itself — one outgoing message that carries both the acknowledgment and the offer, not a separate follow-up.
- Fallback timing: this behavior is superseded for MVP by D031; no scheduled fallback is sent.
- Offer actions: exactly three — "Everything logged", "Add steps", and "Later".
- "Later": dismiss the offer for that day with no automatic reschedule and no second prompt.
- Activity capture: until Apple Health integration exists, "Add steps" asks for the day's steps in-flow and records them as an ordinary daily-steps observation (set or increment) reusing W017.
- Suppression: after conversational closure or an explicit completion, no further completion button is offered. Late food additions after closure keep the day complete without a new check-in.

## Alternatives and consequences

Bundling the offer into the dinner acknowledgment keeps a single outgoing message and avoids a duplicate reminder, matching the data-model outbox note. Excluding scheduled reminders removes the scheduler, DST, outage catch-up, and scheduled-outbox concerns from MVP. "Later" without rescheduling keeps the flow non-nagging. These choices resolve the user-behavior parts of Q06; inline-keyboard and callback delivery mechanics remain technical work for W018.

## References

DAY-001 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); Q06 in [decisions/README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F); section 9 of [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F); [018-combined-check-in.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F).
