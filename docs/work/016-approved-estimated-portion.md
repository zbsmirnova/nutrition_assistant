# W016 — User-approved estimated portion provenance

Status: done.
Milestone: M2.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D028, with D026/D027.

## Outcome and scope

Allow a user to approve an estimated amount for a known, pinned product or saved recipe after the deterministic exact-weight guard asks. Preserve the approval update and display that the resulting portion is estimated.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W016-A01 | Parser clarification answers distinguish an exact quantity from an explicitly approved estimate. |
| W016-A02 | The backend validates one compatible literal amount and an explicit approval marker; a bare confirmation cannot approve an estimate. |
| W016-A03 | Resolved product/recipe commands carry measured or user-approved-estimate provenance and the approval update ID. |
| W016-A04 | PostgreSQL persists provenance with an ownership-safe approval-update foreign key and preserves it through revisions. |
| W016-A05 | Acknowledgments visibly say that an approved amount is an assumption; unknown restaurant nutrition remains pending. |
| W016-A06 | Existing exact food, recipe, clarification, correction, and retry behavior remains compatible. |

## Boundaries

No external nutrition lookup, average restaurant dish, model-generated nutrition, default serving, or standalone `approved_estimate` source component. The existing reserved `EstimatedComponent` remains unused; this slice annotates a known product/recipe quantity.

## Readiness

Implemented in the completion slice and verified on 2026-09-23. The production model contract remains unchanged except for the typed clarification answer and regenerated schemas. PostgreSQL and retained QA passed against the local disposable database; live Nebius and Telegram behavior remain outside this brief. Evidence is recorded in [016-approved-estimated-portion-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/016-approved-estimated-portion-developer.md?type=file&root=%252F). No independent QA review was run for this slice.
