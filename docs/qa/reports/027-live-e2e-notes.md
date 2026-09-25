# W027 — Live E2E notes

Status: in progress.
Date started: 2026-09-25.
Revision under test: `acb1727` (`Clarify Nebius daily observation actions`), on
top of `bbc1c62`.
Evidence source: user-run private Telegram pilot and Nebius smoke. No
independent QA review was run.

## Smoke

At the previous revision, Nebius synthetic smoke passed with `schema_valid: true` and
`expected_action_matched: true`. Parser fingerprint:
`nebius:b6f87aa27acc2bb82e5e9a6a12841b53f606c4290c9d6d80ae6ee5284964006b`.
The prompt has since changed, so smoke and live parser fingerprints must be
rerun for `acb1727`.

## Scenario checklist

| ID | Scenario | Status | Evidence / next action |
| --- | --- | --- | --- |
| E2E-01 | Save a newly provisioned ordinary product through Telegram | pass | Bot confirmed the item and showed central kcal/protein plus ±10% bounds. |
| E2E-02 | Save a known recipe by eaten grams | pass | Telegram processing returned `applied` and `delivery: sent`; the recipe acknowledgement and updated daily kcal/protein were delivered. |
| E2E-03 | Correct an ordinary food quantity in the same entry | pass with UX issue | The correction eventually returned `applied` and recalculated the recipe/day totals. An initial attempt returned `entry_target_not_found`; the correction flow currently depends too much on replying to the bot message. |
| E2E-04 | Set and replace daily weight | pass | Telegram processing returned `applied` and `delivery: sent`; the bot confirmed the current-day weight. |
| E2E-05 | Set and increment daily steps | pending retry on `acb1727` | The first absolute-steps message at the previous revision was accepted by Telegram but ended with `parser_rejected` before mutation or delivery. Retry after the observation prompt clarification, then verify one daily slot and the increment path. |
| E2E-06 | Read today after processing/restart | pending | Request a day summary after a worker restart and compare it with Telegram totals. |
| E2E-07 | Unknown product remains visible and outside totals | pending | Send an unseeded item and verify a visible clarification with no food mutation. |

## UX feedback

| ID | Observation | Proposed follow-up | Status |
| --- | --- | --- | --- |
| UX-01 | Repeating `(оценка lower–upper)` on each nutrient line makes a short acknowledgement feel heavy. | Keep the saved-entry central values clean. Show the uncertainty range once in the daily total, initially on the kcal line; decide separately whether the protein range is shown there. | Open product decision; do not change during this E2E run. |
| UX-02 | It is inconvenient to reply to the bot message for a correction. | When a correction has no explicit target, resolve it against the user's latest bot acknowledgment when it is an unambiguous food entry; keep explicit replies as the stronger target. | Open product decision; implementation after the E2E pass. |

The E2E result is not a general model-quality verdict. It covers the specific
seeded catalog and live transport path exercised above.

## Local verification for the prompt clarification

Developer checks passed on `acb1727`: `tests.test_nebius` and
`tests.test_interpretation` (47 tests), plus `git diff --check`. No independent
QA review was run.

### E2E-05 attempt

The first absolute-steps attempt was polled and accepted by Telegram, but the
conversation worker returned `failed` with `parser_rejected` on its first
attempt. The failure is terminal for that update; no observation mutation or
Telegram delivery was reported. A new message with explicit observation wording
is required to distinguish model interpretation sensitivity from the already
verified observation backend.
