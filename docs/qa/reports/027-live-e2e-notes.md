# W027 — Live E2E notes

Status: complete for the user-run single-user pilot validation.
Date started: 2026-09-25.
Revision under test: `18635ca` (`Apply E2E acknowledgment UX feedback`), on top
of `a8911e6` and the earlier validation revisions.
Evidence source: user-run private Telegram pilot and Nebius smoke. No
independent QA review was run.

The W027 live validation scenarios are complete for the seeded personal
catalog and the bounded Telegram/Nebius path. This closes the current
validation gate with the limitations below; it is not a broad model-quality
benchmark or an independent QA verdict.

## Smoke

On `a8911e6`, Nebius synthetic smoke passed with `schema_valid: true` and
`expected_action_matched: true`. Parser fingerprint:
`nebius:beebab053d79c8de8c25f10d403f444e7f954906fe63b99b0e3e0d38e5ab612f`.

## Scenario checklist

| ID | Scenario | Status | Evidence / next action |
| --- | --- | --- | --- |
| E2E-01 | Save a newly provisioned ordinary product through Telegram | pass | Bot confirmed the item and showed central kcal/protein plus ±10% bounds. |
| E2E-02 | Save a known recipe by eaten grams | pass | Telegram processing returned `applied` and `delivery: sent`; the recipe acknowledgement and updated daily kcal/protein were delivered. |
| E2E-03 | Correct an ordinary food quantity in the same entry | pass with UX issue | The correction eventually returned `applied` and recalculated the recipe/day totals. An initial attempt returned `entry_target_not_found`; the correction flow currently depends too much on replying to the bot message. |
| E2E-04 | Set and replace daily weight | pass | Telegram processing returned `applied` and `delivery: sent`; the bot confirmed the current-day weight. |
| E2E-05 | Set and increment daily steps | pass, cumulative total observed | The absolute set returned `applied` and `delivery: sent` with 8200 steps. A shorthand increment also returned `applied` and `delivery: sent`; the bot reported 17000, consistent with two prior +4400 increments accumulated on the same daily slot. The stored value is normalized; confirmations now use compact thousands formatting. |
| E2E-06 | Read today after processing/restart | pass with UX feedback applied | A new day-summary request returned `applied` and `delivery: sent`; Telegram read back 166 kcal and 4,05 g protein, matching the accumulated entries. Daily summaries now render available kcal/protein ranges. |
| E2E-07 | Unknown product remains visible and outside totals | pass after prompt retry | The first attempt was misclassified as a day summary. On retry, Telegram processing returned `unresolved` with `product_unresolved` and `delivery: sent`; the bot asked for a name or catalog addition and explicitly kept the item out of totals. |

## UX feedback

| ID | Observation | Proposed follow-up | Status |
| --- | --- | --- | --- |
| UX-01 | Repeating `(оценка lower–upper)` on each nutrient line makes a short acknowledgement feel heavy. | Keep the saved-entry central values clean. Show the uncertainty range once in the daily total, initially on the kcal line; decide separately whether the protein range is shown there. | Applied in `18635ca`; both daily kcal and protein ranges are shown when stored. |
| UX-02 | It is inconvenient to reply to the bot message for a correction. | When a correction has no explicit target, resolve it against the user's latest bot acknowledgment when it is an unambiguous food entry; keep explicit replies as the stronger target. | Open product decision; implementation after the E2E pass. |
| UX-03 | The steps confirmation does not need the calendar date for the current day. | Render current-day confirmation without the date, while retaining dates for backdated observations. | Applied in `18635ca`; backdated observations retain their date. |
| UX-04 | A confirmation rendered as `4400 шагов` loses the user's compact input form. | Render shorthand input as `4,4 тыс. шагов` in the confirmation while persisting the normalized integer `4400`. | Applied in `18635ca`; exact integers remain persisted. |
| UX-05 | The daily readback shows only central kcal/protein values. | Show the stored kcal and protein ranges in the daily summary, with the central values retained for readability. | Applied in `18635ca`. |
| UX-06 | A three-item breakfast list was accepted by Telegram but ended with `unsupported` and no delivery. | Keep list messages outside MVP and document one-item-per-message input; design bounded multi-product processing for V2. | Recorded in D052. |
| UX-07 | `яблоко 200 гр` was answered with an exact-weight clarification even though the source states one explicit gram amount. | Accept the common `гр` abbreviation as an exact gram unit; retain the backend guard for genuinely approximate or ambiguous amounts. | Fixed locally; redeploy and rerun this Telegram case. |
| UX-08 | A standalone reply `200` did not resume the pending weight question. | For the current MVP test, reply to the original food message and include the unit (`200 г`); later decide whether an active pending question may accept a standalone bare number or a reply to the bot's clarification. | Open MVP UX issue. |

The E2E result is not a general model-quality verdict. It covers the specific
seeded catalog and live transport path exercised above.

## Local verification for the prompt clarification

Developer checks passed on `18635ca`: 127 offline tests, 14 PostgreSQL
observation integration tests, and `git diff --check`. No independent
QA review was run.

### E2E-05 attempt

The first absolute-steps attempt was polled and accepted by Telegram, but the
conversation worker returned `failed` with `parser_rejected` on its first
attempt. The failure is terminal for that update; no observation mutation or
Telegram delivery was reported. A new message with explicit observation wording
is required to distinguish model interpretation sensitivity from the already
verified observation backend.
