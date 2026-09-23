# W007 — Save the clear item in a mixed food message

Status: done.
Milestone: M2.
Owner: lead assistant, architect/developer; developer verification complete.
Updated: 2026-09-23.

## Outcome and scope

For one message containing two independent food actions, save the clear product item immediately and keep one unresolved dairy-fat item outside totals. When the user replies with the missing fat percentage, resume only that pending action. The first entry must retain its identity and must not be added again.

The bounded implementation supports exactly one ready product-food action and one unresolved dairy-fat action. It does not implement arbitrary multi-action execution, recipe dependencies, multiple pending items, mixed corrections, or general quantity clarification.

## Requirements and decisions

FOOD-004, FOOD-002/003, DATA-002/003, and CALC-001 govern this slice. D016 extends stable command identities to action positions while preserving position-zero compatibility. D015 supplies the pending question and reply-link behavior. Evidence excerpts are action-local for resolution; the original Telegram update remains the source of all operation identities.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W007-A01 | A two-action proposal with one clear product and one dairy-fat-unresolved action saves exactly the clear item and records one pending question. |
| W007-A02 | The resolver checks each action's own evidence excerpt; a second quantity cannot satisfy the first or second action accidentally. |
| W007-A03 | The clear operation uses position zero and can be replayed without another parser call or food entry. |
| W007-A04 | A reply to the original message resolves the stored pending action at its original position, creating exactly one additional entry and clearing the pending count. |
| W007-A05 | A crash/retry or duplicate reply cannot reapply either operation or replace the frozen proposal. |
| W007-A06 | Existing single-food, clarification, migration, ownership, provider, and transport checks remain green. |

## Implementation checklist

- [x] Generalize stable operation IDs and prepared-operation position validation to positions 0–31.
- [x] Resolve action evidence independently and accept one ready plus one dairy-pending action.
- [x] Preserve pending position/context and resume the pending operation through W006's reply path.
- [x] Add PostgreSQL coverage for partial save, pending count, position-one resume, and replay.
- [x] Run the complete integration/retained QA suites and record the exact revision.
- [x] Commit the completed slice with maintained documentation and QA evidence.

## Developer handoff

Implementation is committed in `13f0b63`. Offline tests pass (`96` tests), PostgreSQL integration passes (`61` tests), and retained QA passes (`32` checks). No schema migration is needed; this slice changes operation identity validation and worker behavior only.

## QA result and completion

Developer verification passes for the bounded mixed-food workflow. Evidence is in [007-mixed-food-partial-saving-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/007-mixed-food-partial-saving-developer.md?type=file&root=%252F). No independent W007 review, live Nebius, or real Telegram behavior is claimed.
