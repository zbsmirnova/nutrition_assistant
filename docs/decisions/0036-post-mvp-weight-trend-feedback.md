# D036 — Post-MVP weight trend feedback

Kind: product.
Status: accepted for post-MVP reporting.
Recorded: 2026-09-24.
Decision owner: product owner.
Acceptance evidence: explicit user decision in the project discussion.
Related questions: exact coverage and wording remain part of M5 reporting design.

## Context

The MVP records one revisable body-weight value per user and local date. A single acknowledgment is useful for recording the value, but trend interpretation needs several prior observations and should not complicate the MVP write path.

## Decision

After MVP, provide concise feedback on the current weight trend by comparing the current value with available measurements from the previous 4–7 local days. Keep this as reporting feedback, separate from the durable observation write and from nutrition or exercise judgment.

The M5 design must define behavior when fewer than four prior measurements exist, when dates are missing, and how the comparison is worded. It must remain nonjudgmental and must not present a trend as medical advice.

## Alternatives and consequences

Showing no trend keeps MVP simpler but misses useful context once history exists. Calculating a trend during every observation write would couple recording to reporting and make partial history harder to explain. Deferring the comparison to post-MVP reporting keeps the current write path deterministic and lets the product choose coverage and wording with the daily/weekly reports.

## References and replacement history

Related work: [W017](../work/017-daily-observations.md), [W018](../work/018-combined-check-in.md), and [roadmap](../roadmap.md). No previous decision is superseded.
