# D002 — Durable command execution and response intent

Kind: technical.
Status: accepted for M1; later conversational workflows remain scoped to M2.
Recorded and updated: 2026-09-22.
Decision owner: lead architect under the user's authorization to implement the first persistence slice.
Acceptance evidence: the user authorized proceeding after the proposed first-slice outcome and checks were described. This is a delegated technical decision, not a claim that the user selected a particular locking primitive.
Related questions: Q01 resolved for M1; Q04 remains open for conversation behavior.

## Context

Duplicate deliveries, crashes after commit, partial messages, delayed clarification, and concurrent corrections must not create extra portions or stale overwrites. Provider calls and transport delivery can fail independently of the database.

## Decision and implemented boundary

1. Durably accept messages from an already authenticated internal actor and its mapped Telegram account. Enforce bot-wide uniqueness of the Telegram update identity, plus matching user/account/bot foreign keys. Changed payloads under an existing identity fail; distinct messages are not deduplicated by text.
2. M1 freezes exactly one resolved add-food command per message, position zero. Its backend-assigned UUID is stable from the inbox ID and position. The complete command, source evidence, and request hash are immutable in prepared operations. Reuse with a changed envelope is rejected.
3. Use PostgreSQL READ COMMITTED with a user-row FOR UPDATE lock for each short prepare/apply transaction. Read services take a user-row share lock for consistent multi-query summaries. No external work occurs while those locks are held.
4. On execution, reload the stored command, check actor/source/reference ownership, and recalculate from immutable pinned product versions. Commit food revisions/components, current pointers, day/user revision counters, the applied outcome, and one response intent atomically.
5. Replay returns the stored outcome before attempting another mutation. Its day summary is the historical command result; a separate day query returns current totals.
6. Fully resolved M1 additions commute even when the observed context revision has advanced: the backend revalidates their explicit date, quantity basis, and immutable references under the lock, then derives current totals. It never substitutes newer catalog values or overwrites another addition. State-dependent corrections and interpretation re-resolution are M2 work.
7. Claim a committed response in a separate short transaction. Send outside the transaction; acknowledge with a claim token and unexpired lease. An expired claim or uncertain external outcome becomes uncertain without automatic resend. Proven pre-send failures get at most three attempts.
8. The initial delivery adapter is a fake. No actual Telegram authentication, send, provider call, pending conversation, or dependency-group workflow is implemented by M1.

User-row locking replaces the earlier proposed long-lived user-processing lease for this synchronous slice. A separate processing lease/fencing design remains a possible M2 choice if work spans provider calls; no lock is held while waiting for a user.

## Alternatives and consequences

In-memory locks cannot protect restarts or several processes. Long transactions spanning providers would hold locks unpredictably. A separate durable user lease adds failure states that M1 does not need.

One user's writes are serialized, which is acceptable for the initial personal workload. The database enforces owned references and immutable ordinary snapshots; numeric/semantic validation remains in the application. Typed application failures produce no success result or response intent. Invalid prepared input remains inspectable and cannot be replaced silently.

An outbox preserves response intent, not exactly-once visible messages. M1 exposes uncertain/failed states; transport-specific recovery and fresh combined user replies belong to M2. Returning an old operation result does not claim its snapshot is the latest day state.

## Evidence and references

[service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/service.py?type=file&root=%252F); [outbox.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/outbox.py?type=file&root=%252F); [test_food_service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/integration/test_food_service.py?type=file&root=%252F); [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F). Developer checks cover concurrent identical/distinct operations, actual process loss before/after commit, foreign-owner rejection, replay, and uncertain sends. Independent QA evidence is tracked in the work brief.
