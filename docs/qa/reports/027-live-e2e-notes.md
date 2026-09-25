# W027 — Live E2E notes

Status: in progress.
Date started: 2026-09-25.
Revision under test: `a8911e6` (`Keep unknown consumed foods visible`), on top of
`f2157c2`, `b53e15b`, `37718f7`, `acb1727`, and `bbc1c62`.
Evidence source: user-run private Telegram pilot and Nebius smoke. No
independent QA review was run.

## Smoke

At the previous revision, Nebius synthetic smoke passed with `schema_valid: true` and
`expected_action_matched: true`. Parser fingerprint:
`nebius:b6f87aa27acc2bb82e5e9a6a12841b53f606c4290c9d6d80ae6ee5284964006b`.
The prompt and observation date handling have since changed, so smoke and live
parser fingerprints must be rerun for `a8911e6`.

## Scenario checklist

| ID | Scenario | Status | Evidence / next action |
| --- | --- | --- | --- |
| E2E-01 | Save a newly provisioned ordinary product through Telegram | pass | Bot confirmed the item and showed central kcal/protein plus ±10% bounds. |
| E2E-02 | Save a known recipe by eaten grams | pass | Telegram processing returned `applied` and `delivery: sent`; the recipe acknowledgement and updated daily kcal/protein were delivered. |
| E2E-03 | Correct an ordinary food quantity in the same entry | pass with UX issue | The correction eventually returned `applied` and recalculated the recipe/day totals. An initial attempt returned `entry_target_not_found`; the correction flow currently depends too much on replying to the bot message. |
| E2E-04 | Set and replace daily weight | pass | Telegram processing returned `applied` and `delivery: sent`; the bot confirmed the current-day weight. |
| E2E-05 | Set and increment daily steps | pass, cumulative total observed | The absolute set returned `applied` and `delivery: sent` with 8200 steps. A shorthand increment also returned `applied` and `delivery: sent`; the bot reported 17000, consistent with two prior +4400 increments accumulated on the same daily slot. The stored value is normalized, while the confirmation-format UX remains open under UX-04. |
| E2E-06 | Read today after processing/restart | pass with UX feedback | A new day-summary request returned `applied` and `delivery: sent`; Telegram read back 166 kcal and 4,05 g protein, matching the accumulated entries. The current response omits the uncertainty ranges; see UX-05. |
| E2E-07 | Unknown product remains visible and outside totals | pass after prompt retry | The first attempt was misclassified as a day summary. On retry, Telegram processing returned `unresolved` with `product_unresolved` and `delivery: sent`; the bot asked for a name or catalog addition and explicitly kept the item out of totals. |

## UX feedback

| ID | Observation | Proposed follow-up | Status |
| --- | --- | --- | --- |
| UX-01 | Repeating `(оценка lower–upper)` on each nutrient line makes a short acknowledgement feel heavy. | Keep the saved-entry central values clean. Show the uncertainty range once in the daily total, initially on the kcal line; decide separately whether the protein range is shown there. | Open product decision; do not change during this E2E run. |
| UX-02 | It is inconvenient to reply to the bot message for a correction. | When a correction has no explicit target, resolve it against the user's latest bot acknowledgment when it is an unambiguous food entry; keep explicit replies as the stronger target. | Open product decision; implementation after the E2E pass. |
| UX-03 | The steps confirmation does not need the calendar date for the current day. | Render current-day confirmation without the date, while retaining dates for backdated observations. | Open product decision; do not change during this E2E run. |
| UX-04 | A confirmation rendered as `4400 шагов` loses the user's compact input form. | Render shorthand input as `4,4 тыс. шагов` in the confirmation while persisting the normalized integer `4400`. | Open product decision; do not change during this E2E run. |
| UX-05 | The daily readback shows only central kcal/protein values. | Show the stored kcal and protein ranges in the daily summary, with the central values retained for readability. | Open product decision; do not change during this E2E run. |

The E2E result is not a general model-quality verdict. It covers the specific
seeded catalog and live transport path exercised above.

## Local verification for the prompt clarification

Developer checks passed on `a8911e6`: `tests.test_nebius` and
`tests.test_interpretation` (48 tests), plus `git diff --check`. No independent
QA review was run.

### E2E-05 attempt

The first absolute-steps attempt was polled and accepted by Telegram, but the
conversation worker returned `failed` with `parser_rejected` on its first
attempt. The failure is terminal for that update; no observation mutation or
Telegram delivery was reported. A new message with explicit observation wording
is required to distinguish model interpretation sensitivity from the already
verified observation backend.
