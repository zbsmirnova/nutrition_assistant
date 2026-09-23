# W014 — Recipe ambiguity and eaten-grams clarification

Status: ready.
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

Product behavior is accepted in D024. Implementation can proceed without another product decision; the typed answer contract and clarification-rendering details are the next technical design step.
