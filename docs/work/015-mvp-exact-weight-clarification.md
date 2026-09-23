# W015 — MVP exact-weight clarification guard

Status: done.
Milestone: M2.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D026 and D027.

## Outcome and scope

Make the backend enforce the MVP rule that nutrition-affecting weight ambiguity is a user decision. A complete-looking parser proposal is held when the source says an amount is approximate, uses a range/bound, reverses the quantity wording, or gives gross/bone/skin wording without a usable-weight basis. A pending product or recipe action receives a typed quantity question. The user must supply the portion amount (normally in grams; a compatible millilitre amount remains valid for a volume-based product), either as an exact value or as an explicitly approved estimate. The model and backend must never invent that amount. An exact quantity reply can resume the original action while preserving the original evidence and operation context.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W015-A01 | Approximate, bounded, reversed-colloquial, gross, and bone/skin weights do not create a food command. |
| W015-A02 | Candidate-backed deferrals persist a quantity question that asks the user to provide exact usable grams or an explicitly approved approximate gram amount. |
| W015-A03 | The worker wording explains that an unapproved approximate weight stays outside the total. |
| W015-A04 | A typed exact quantity answer can resume an original approximate action without re-triggering the original ambiguity marker. |
| W015-A05 | Assumption approval/provenance is not silently treated as measured data; W016 implements the follow-on typed approval and visible provenance path. |

## Boundaries

No new parser schema, live model call, migration, automatic serving conversion, average product selection, recipe substitution, or assumption persistence within W015 itself. The production model contract remains unchanged. The guard is deterministic and authoritative after model interpretation. W016 is the separate follow-on that persists an explicitly approved amount for a known product or recipe.

## Developer handoff and completion

Implemented in the resolver and worker with focused offline tests. The exact revision and test evidence are recorded in [015-mvp-exact-weight-clarification-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/015-mvp-exact-weight-clarification-developer.md?type=file&root=%252F). No independent QA review or live model/Telegram behavior is claimed.
