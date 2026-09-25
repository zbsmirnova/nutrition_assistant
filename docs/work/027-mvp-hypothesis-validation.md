# W027 — MVP hypothesis validation: stable calculation and recording

Status: in progress.
Milestone: MVP-GATE.
Owner: lead assistant, architect/developer; QA evidence must remain separately attributed.
Decision: D049.

## Hypothesis

For one private Telegram user, ordinary Russian food messages that refer to a
small owner-scoped personal catalog can be interpreted, calculated, and saved
reliably enough for daily use. “Reliable” means that accepted records are not
lost or duplicated, corrections preserve entry identity, and totals can be
reconciled from durable entries after retries and restart. It does not claim
laboratory nutrition accuracy or validate unknown restaurant estimates.

## Validation setup

- Use a disposable PostgreSQL schema and a fresh owner.
- Seed a small product set and at least one recipe through W021/W022.
- Use the selected Nebius model and record the model, prompt, parser fingerprint,
  migration head, and commit under review.
- Keep unknown products and restaurant messages out of the core scorecard;
  record any such probe as an explicitly excluded experiment.
- Run the same scenarios through the bounded worker and, when credentials and
  deployment are available, through the private Telegram path.

## Core scenarios

| ID | Scenario | Expected evidence |
| --- | --- | --- |
| W027-01 | Add one seeded product with an exact gram amount | One applied operation, one food-entry identity, central nutrition and bounds, daily total equal to the entry. |
| W027-02 | Add a seeded saved recipe with eaten grams | One applied operation pinned to the recipe version; calculated nutrition is scaled from the stored per-100-g profile. |
| W027-03 | Add several meals on one date | Each distinct source is retained once; daily kcal/protein bounds equal the sum of included entry bounds. |
| W027-04 | Correct 100 g to 80 g | The same logical entry is revised, no second portion is created, and the day total changes by the expected delta. |
| W027-05 | Replay the same Telegram update and repeat after a worker restart | No duplicate domain mutation; the final entry and total are unchanged. |
| W027-06 | Fail before and after the domain commit, then retry | A pre-commit failure leaves no mutation; a post-commit retry returns the committed result without applying it twice. |
| W027-07 | Query today and a previous date after processing and restart | The readback matches the durable entries and their pinned nutrition versions. |
| W027-08 | Send an unknown product or restaurant dish without a seeded identity | The item stays visibly unresolved and outside totals; the result is excluded from the core scorecard. |
| W027-09 | Set and replace daily weight; set and increment steps | Observation behavior is recorded separately from the food hypothesis and does not alter food totals. |

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W027-A01 | Every accepted core food message has exactly one durable operation outcome and one corresponding entry revision. |
| W027-A02 | Replays, retries, and worker restarts produce zero duplicate food mutations. |
| W027-A03 | A correction updates the existing entry identity and preserves revision history. |
| W027-A04 | For every completed scenario, backend daily totals reconcile with the included entry snapshots, including lower/upper bounds. |
| W027-A05 | A day/date readback is available after processing and restart and matches the database state. |
| W027-A06 | Unknown and restaurant probes cannot change the core totals and are clearly marked as excluded from the verdict. |
| W027-A07 | The report distinguishes developer verification, independent QA, live Telegram evidence, and live-model interpretation quality. |

## Proposed scorecard

These are proposed release-gate targets for the first run, not a claim that
they have already been accepted or achieved:

- zero lost accepted entries;
- zero duplicate mutations in replay/restart scenarios;
- 100% arithmetic reconciliation for committed core entries;
- 100% same-entry identity preservation for corrections;
- no silent conversion of unresolved items into totals;
- interpretation success and clarification rates reported separately, with no
  model-quality verdict inferred from persistence results.

## Out of scope

Telegram product creation, Telegram recipe authoring, unknown-food LLM
estimates, restaurant estimates, Open Food Facts/USDA lookup, progress reports,
reminders, close-day behavior, feedback capture, photos, barcodes, Apple
Health, multi-user access, and deployment readiness. Product creation is the
next slice after this gate so the personal database can grow through the bot.

## Handoff and report

Before marking this brief done, record the exact revision, environment,
migration, fixture identities, commands, scenario results, failures, and
coverage limits in a QA report linked here. A live user run is useful evidence
but is not an independent QA review. The W024 deployment brief remains the
separate personal-release gate after this validation.

## Implementation progress

The production Telegram path now excludes external catalog lookup, and
`get_day_summary` is resolved, persisted, replay-safe, and rendered through the
same operation/outbox flow as food mutations. The remaining gate work is the
full scenario run with seeded products and recipes, including live Telegram
evidence and a separate interpretation-quality report.
