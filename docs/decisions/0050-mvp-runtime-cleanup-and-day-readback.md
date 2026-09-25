# D050 — MVP runtime cleanup and durable day readback

Kind: technical.
Status: accepted for the MVP validation slice.
Recorded: 2026-09-25.
Decision owner: lead assistant under the accepted D049 MVP boundary.

## Decision

The production Telegram worker uses only the owner-scoped catalog, resolver,
durable command, and outbox path required by D049. Open Food Facts and USDA
lookup remain available only as isolated future experiment code and are no
longer constructed by the CLI or the long-running pilot runner. An unresolved
unknown food therefore remains unresolved and cannot change totals.

Day readback is a first-class typed `get_day_summary` command. The resolver
derives the effective local date from the source message, the service freezes
and records the read operation through the same applied-operation and outbox
tables as mutations, and Telegram renders only the MVP-facing kcal and protein
lines. Fat and carbohydrates remain in the stored `DailySummary`.

## Rationale

The external lookup path had produced misleading candidates for Russian food
names and made persistence failures depend on a network provider. Keeping it
out of the validation path makes the MVP hypothesis measurable and leaves the
later source experiment replaceable. Using the normal durable operation path
for readback verifies that a user can check the database state after retries or
restart without introducing a second consistency mechanism.

## Consequences

The core validation gate must use products and recipes seeded through the
trusted local commands. Unknown and restaurant messages are excluded probes.
The day summary output is intentionally small; future progress reports and
full macro views can consume the same backend summary without changing food
entry persistence.

## References

See [D049](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0049-mvp-validation-boundary.md?type=file&root=%252F), [W027](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/027-mvp-hypothesis-validation.md?type=file&root=%252F), and [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F).
