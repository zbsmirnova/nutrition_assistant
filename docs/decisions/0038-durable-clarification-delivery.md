# D038 — Durable Telegram clarification delivery

Status: Accepted for MVP implementation  
Recorded: 2026-09-24  
Authority: architect decision within the accepted MVP clarification policy D026/D027

## Decision

When the conversation worker holds a message for a supported clarification, it
persists the user-facing question as a normal durable outbox payload in the
same transaction as the pending job. The existing outbox sender delivers the
question as a reply to the original Telegram source and applies its existing
retry, lease, and uncertain-send rules.

The notification is a typed `needs_clarification` outcome. It uses a separate
deterministic notification UUID namespace and the reserved internal prepared
operation position 31. This avoids a schema migration and keeps notification
identity separate from food command identities. Replays cannot create a second
question for the same source. Pending food remains outside totals until the
user answers.

This covers typed dairy-fat, materially uncertain quantity, and ambiguous saved
recipe questions. Unknown restaurant nutrition or unresolved catalog identity
still has no nutrition write and requires a later source decision. Scheduled
reminders, callbacks, and close-day behavior remain post-MVP W018.

## Consequences

- A pending clarification is visible and retryable through the same delivery
  path as a committed food acknowledgement.
- The question is an operational notification, not a nutrition mutation.
- Position 31 is reserved for this internal notification path and must not be
  used for a normal parser action in future multi-action expansion.
- Live Nebius and Telegram behavior still require a user-run pilot; current
  PostgreSQL, rendering, and transport checks are developer evidence only.

## Verification

The implementation is covered by W023 and the recorded developer suites. No
independent QA review is claimed for this decision.
