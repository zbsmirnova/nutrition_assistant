# D030 — Combined completion/activity check-in behavior

Kind: product
Status: accepted for W018
Recorded: 2026-09-23.
Decision owner: product owner (answers to Q06), recorded by the lead assistant.

## Decision

The combined completion/activity check-in behaves as follows:

- Dinner trigger: when a meal is recognized as dinner, the check-in is offered on the dinner food acknowledgment itself — one outgoing message that carries both the acknowledgment and the offer, not a separate follow-up.
- Fallback timing: if no dinner is recorded for the local day, the check-in is offered at 21:00 local time. If that moment passed while the service was offline, the fallback is skipped for that day rather than sent late.
- Offer actions: exactly three — "Everything logged", "Add steps", and "Later".
- "Later": dismiss the offer for that day with no automatic reschedule and no second prompt.
- Activity capture: until Apple Health integration exists, "Add steps" asks for the day's steps in-flow and records them as an ordinary daily-steps observation (set or increment) reusing W017.
- Suppression: after conversational closure or an explicit completion, no further completion button is offered. A 21:00 fallback followed by a later dinner does not create a second logical offer. Late food additions after closure keep the day complete without a new check-in.

## Alternatives and consequences

Bundling the offer into the dinner acknowledgment keeps a single outgoing message and avoids a duplicate reminder, matching the data-model outbox note. Skipping a missed 21:00 fallback (rather than catching up late) avoids a stale next-day prompt at the cost of no late-evening nudge after an outage. "Later" without rescheduling matches the proposed Q06 default and keeps the flow non-nagging. These choices resolve the user-behavior parts of Q06; the delivery mechanics (inline keyboard, callback handling, one-logical-offer idempotency across retries/races, and the local-time scheduler with DST) remain a technical decision for the W018 implementation slice.

## References

DAY-001 in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F); Q06 in [decisions/README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F); section 9 of [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F); [018-combined-check-in.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F).
