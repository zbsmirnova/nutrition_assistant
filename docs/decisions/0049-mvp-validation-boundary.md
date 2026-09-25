# D049 — MVP validation boundary and personal catalog growth

Kind: product/technical.
Status: accepted for the MVP validation gate.
Recorded: 2026-09-25.
Decision owner: product owner.
Acceptance evidence: explicit confirmation that the first MVP pass validates
calculation and durable recording with seeded personal data; unknown and
restaurant estimates are a separate experiment.

## Context

The product hypothesis is that free-form Telegram food messages can be turned
into useful calorie and macronutrient records without losing or duplicating
entries. The earlier MVP scope combined that hypothesis with unknown-food
estimation, restaurant uncertainty, catalog editing, reports, reminders, and
observations. That made a failure difficult to attribute and left the runtime
and documents with competing source policies.

## Decision

The first release gate is a narrow **MVP validation slice**:

- one private Telegram user and the durable inbox, worker, command, revision,
  result, and outbox path;
- consumption of owner-scoped products and saved recipes preloaded through the
  trusted local provisioning commands;
- free-form food logging, same-entry corrections, retries, restart recovery,
  and daily totals;
- central nutrition plus backend-calculated kcal/protein ranges in the daily
  result, with all four nutrient fields retained in storage;
- a read-only day/date summary so the owner can verify that records remain
  present after processing and restart.

Weight and steps remain supported as an adjacent MVP capability and are tested
separately; they do not decide the calorie-recording hypothesis.

Unknown products and restaurant dishes are not part of the core release gate.
They remain an explicitly separate experiment. The external Open Food Facts and
USDA lookup path is disabled for the validation slice, and an unresolved
unknown item must not change totals. D047's ±10% ordinary and ±25% restaurant
coefficients remain available for that later experiment, but do not make its
model quality a core MVP verdict.

After the validation gate, the first catalog-growth slice adds Telegram product
creation from label values. It must create versioned owner-scoped products and
reuse the same deterministic logging path. Recipe creation through Telegram is
a separate follow-up; the validation gate uses the trusted recipe fixture path.

## Validation definition

The gate is concerned with stability, not laboratory accuracy. Its proposed
targets are zero lost accepted entries, zero duplicate mutations on replay or
restart, exact daily-total reconciliation with committed entries, and
successful same-entry correction. Interpretation coverage and model quality are
reported separately from persistence evidence.

## Consequences

This boundary makes a clean failure diagnosis possible. It also means that the
first pilot deliberately starts with a small personal catalog and grows it
through the bot in the next slice. Restaurant and unknown-food behavior can be
changed without invalidating the persistence evidence.

## References

See [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), and [027-mvp-hypothesis-validation.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/027-mvp-hypothesis-validation.md?type=file&root=%252F).
