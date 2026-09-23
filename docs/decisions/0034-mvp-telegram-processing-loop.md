# D034 — Add a bounded Telegram pilot loop

Kind: Technical.
Status: accepted for MVP implementation.
Recorded: 2026-09-23.
Decision owner: architect/developer under the approved MVP acceleration plan.
Related decisions: D002, D007, D011, D012, D032, D033.

## Decision

Provide an explicit `telegram-process` operator command for the single-owner MVP pilot. One invocation verifies the configured bot, polls one bounded Telegram batch, processes the owner's oldest eligible inbox source through the configured Nebius parser, and dispatches one queued Telegram response. Existing `telegram-poll`, `conversation-nebius`, and `telegram-send` commands remain available for diagnosis and recovery.

The command does not become a background daemon, does not process another user's messages, does not bypass durable conversation-job claims or outbox leases, and does not add scheduling. Its output contains only poll counts, bounded processing status, source UUID, and delivery status; it never prints source text, clarification wording, food outcomes, provider payloads, or credentials.

## Rationale and limits

The existing components already implement polling, provider interpretation, durable worker recovery, and outbox delivery, but required manual source-ID handoff for every test. A bounded composition removes that friction while preserving the existing transaction and retry boundaries. Multi-user orchestration, continuous workers, callbacks, and reminders remain future deployment/scheduling work.

## References

[W020](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/020-telegram-processing-loop.md?type=file&root=%252F), [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F).
