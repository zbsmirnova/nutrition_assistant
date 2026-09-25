# W026 — Post-MVP restaurant calorie estimation

Status: planned.
Milestone: post-MVP personal release / M6 readiness.
Owner: lead assistant, with product owner validation.
Decision: D045.

## Goal

Let a user record an unfamiliar restaurant meal with a clearly labeled,
reference-based calorie estimate when exact nutrition is unavailable and
weighing is uncomfortable.

## Planned behavior

1. Identify the dish, cuisine/context, and rough eaten portion.
2. Search an approved nutrition reference source for similar foods.
3. Calculate the reference average and propose a range from that average to
   average plus 30 percent.
4. Explain that the upper margin accounts for possible hidden restaurant fats.
5. Ask the user to approve the range or correct the dish/portion.
6. Save the selected estimate with source, portion, range, approval, and
   visible estimated provenance.
7. Reuse a later confirmed personal interpretation without rewriting prior
   history.

## Out of scope

Exact restaurant nutrition, photo-based portion estimation, silent provider
selection, automatic approval, and treating the 30 percent margin as a
validated universal correction factor.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W026-A01 | An unfamiliar restaurant meal can produce a bounded reference-based proposal without creating a food entry before approval. |
| W026-A02 | The proposal shows the source basis, portion assumption, average, upper range, and estimated status. |
| W026-A03 | The user can approve, correct, or cancel the proposal; only an approved result enters totals. |
| W026-A04 | The persisted entry retains source references, range, approval evidence, and estimate provenance. |
| W026-A05 | Evaluation measures whether the average-to-plus-30% range is useful across cuisines and restaurant contexts; the result can revise D045. |

## Dependencies and validation

Choose a licensed reference provider and confirm regional restaurant coverage.
Create a held-out evaluation set with synthetic and user-approved examples;
keep private messages and credentials out of fixtures and reports. Validate the
range and UX during the personal pilot before considering broader release.
