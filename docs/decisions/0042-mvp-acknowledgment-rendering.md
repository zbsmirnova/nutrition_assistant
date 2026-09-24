# D042 — MVP Telegram acknowledgment rendering

Status: Accepted for MVP
Recorded: 2026-09-24
Authority: product-owner decision during E2E testing
Related work: W017, W020

## Decision

Routine Telegram confirmations are concise and user-focused:

- Food confirmations use `Итого за сегодня:` and show kcal/protein for the
  saved or corrected entry and the updated daily total.
- Fat and carbohydrate values continue to be calculated and persisted, but
  are hidden from routine Telegram food confirmations.
- Pending-clarification counts and day-completeness sentences are omitted from
  routine food confirmations. Pending actions remain outside totals.
- A weight confirmation uses `Вес за сегодня записан: 76,3 кг.`. Steps keep
  their existing dated confirmation wording until a separate product decision.

This changes presentation only. It does not change storage, nutrient
calculation, pending-state behavior, observation dates, revision history, or
the MVP rule that there is no close-day command.

## Rationale

E2E testing showed that the dated total and repeated status lines add noise to
ordinary meal logging. The user still needs kcal/protein feedback, while the
remaining nutrient fields and workflow state must stay available in the
authoritative result and database for later summaries and corrections.
