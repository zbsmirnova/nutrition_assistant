# D051 — E2E acknowledgment refinement

Kind: Product/technical.
Status: Accepted for MVP.
Recorded: 2026-09-25.
Authority: product-owner feedback during the W027 live E2E run.
Related decisions: D042, D049, D050.

## Decision

Apply the following presentation rules to routine Telegram acknowledgments:

- A saved or corrected food entry shows central kcal and protein values only.
- The updated daily kcal and protein totals show their available lower/upper
  ranges. If a range is absent in the stored result, show the central value
  without inventing bounds. Fat and carbohydrates remain hidden in routine
  replies while staying persisted in the result and database.
- A current-day steps confirmation omits the calendar date and uses a compact
  thousands form such as `4,4 тыс. шагов`; the persisted value remains the
  exact integer `4400`.
- A backdated steps confirmation keeps its date and uses the same compact
  number form.

This is a rendering-only change. It does not alter parser actions, observation
storage, nutrition arithmetic, uncertainty bounds, or day identity.

## Rationale

The live E2E run showed that repeating ranges on each entry nutrient line made
acknowledgments heavy, while the daily total is the useful place to inspect
uncertainty. It also showed that a date on a current-day steps confirmation is
noise and that displaying normalized `4400` loses the user's compact scale.

## Consequences

Renderer tests must cover central entry values, ranged daily totals, current-day
and backdated steps, and compact thousand formatting. No migration or contract
schema change is required.

## References

[W027 live E2E notes](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/027-live-e2e-notes.md?type=file&root=%252F), [D042](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0042-mvp-acknowledgment-rendering.md?type=file&root=%252F).
