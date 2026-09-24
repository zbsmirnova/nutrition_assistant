# W025 — External food catalog fallback and personal cache

Status: complete for the bounded MVP fallback. Owner: lead assistant. Milestone: M2 / MVP pilot.

## Goal

Make a first-time unknown product usable without allowing a provider or model
to write a diary entry. Local products are still preferred. A provider result
is cached as an immutable, unconfirmed product snapshot; the user selects it
and approves the portion before the normal deterministic food command runs.

## Scope

- Open Food Facts adapter with bounded search, nutrient mapping, provenance, and
  a required identifying `User-Agent`.
- Optional USDA FoodData Central adapter enabled by `USDA_FDC_API_KEY`.
- Provider failure and rate-limit-safe retry behavior; no provider payload in
  ordinary operator output.
- Owner-scoped external source snapshots and a separate product-confirmation
  record, so source rows remain immutable.
- Numbered candidate clarification followed by the existing exact-weight or
  user-approved-estimate clarification.
- Reuse of a confirmed local version on later messages.
- A model proposal that marks only the food identity as unresolved, or selects
  a conflicting local identity, may enter the external lookup path when its
  quantity, date, and basis are otherwise complete. Other unresolved fields
  remain pending.

Out of scope: restaurants and unverified nutrition averages, barcode/photo
flows, bulk imports, background synchronization, aliases, and recipes that
need external ingredient resolution. Unknown restaurant nutrition remains
pending.

## Acceptance criteria

| ID | Criterion |
| --- | --- |
| W025-A01 | Local candidates resolve before any external call; the external query contains only the bounded food term selected by the interpretation. |
| W025-A02 | Injected Open Food Facts and USDA responses map only usable per-100-g nutrition and preserve provider/external identifiers, basis, and license. |
| W025-A03 | A provider result creates no food entry and remains hidden from ordinary catalog context until the user selects it. |
| W025-A04 | Selection is durable, resumes the original operation, records confirmation separately from the immutable source snapshot, and enforces the existing exact/approved portion rule for approximate or missing weights. |
| W025-A05 | A confirmed version is reused locally; provider outage is retryable; empty or unsuitable results remain unresolved without changing totals. |
| W025-A06 | Source adapter unit tests, PostgreSQL migration/worker tests, offline regression tests, and `git diff --check` pass. |
| W025-A07 | A name-based proposal with only an identity unresolved, or a conflicting local identity, searches the configured external catalog; unresolved quantity, date, basis, or dependencies do not bypass backend guards. |

## Verification

Developer verification is recorded in [025-external-food-catalog-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/025-external-food-catalog-developer.md?type=file&root=%252F). No independent QA review or live provider request was run; those limits remain explicit.
