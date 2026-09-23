# W014 — Recipe ambiguity and eaten-grams clarification

Status: done.
Milestone: M3 / M2.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D024.

## Outcome and scope

Resume a pending saved-recipe food action after the user selects a numbered recipe, types a more specific recipe name, or supplies explicit eaten grams. Preserve the original operation identity, source date, and evidence while creating at most one pinned recipe component.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W014-A01 | Duplicate recipe names produce a user-facing pending question with numbered scoped candidates and an exact-name fallback. |
| W014-A02 | A numeric candidate answer selects exactly one owned recipe and resumes the original food action once. |
| W014-A03 | A more specific name answer resolves exactly one recipe or remains pending without mutation. |
| W014-A04 | A missing or serving-style amount asks for explicit grams; the answer resumes without inventing a portion. |
| W014-A05 | Retries, original-date preservation, privacy projection, and independent actions remain safe. |

## Boundaries

No alias table, general recipe search, default portion, batch entity, external database comparison, or live model quality measurement.

## Readiness

Product behavior is accepted in D024. The bounded typed-answer and clarification-rendering implementation is complete; broader recipe aliases and general search remain future work.

## Developer handoff and completion

Implemented pending recipe candidate context, selection/text/quantity answer handling, bounded fuzzy name matching, and user-facing clarification text in the worker result. The parser contract models were unchanged; no schema regeneration or migration was required. Verification is recorded in [014-recipe-clarification-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/014-recipe-clarification-developer.md?type=file&root=%252F). No independent W014 review or live model/Telegram behavior is claimed.
