# QA report — W004 / attempt 1

## Identity and scope

Date: 2026-09-22. Reviewer: independent_m1_qa, separate independent QA.
Verdict: **fail for original W004 snapshot: valid Retry-After whitespace bypasses delay policy**.

Source ID: 3b4ee706e7d0fab4b917d9711c2355da08cba8a3d6f2eb89c56ec64f15fdb205.
Base commit: 7bea583d1f567e0971d48993bccfc59b35d8a5ae.
Archive SHA-256: 078fc093b2ecb4ec0c2cd97bff78452b2fa553258298ffcba004985ef3bb7eb9.
Manifest: [source-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w004-review-mvgeurf2/source-manifest.json?type=file&root=%252F).
QA independently verified all 105 file hashes, archive hash and files-list source-ID formula. No frozen source or main workspace was edited.

Reviewed constitution, W004 A01–A08, D009/D012 and W003 worker requirements; adapter/configuration, prompt projection, response validation, worker failure classification, CLI and relevant tests. Runtime: macOS 26.5.2 arm64; Python 3.14.0; SQLAlchemy 2.0.54; Alembic 1.20.0; psycopg/psycopg-binary 3.3.6; Pydantic 2.13.5; jsonschema 4.26.0. PostgreSQL 17.11 is the supplied local database environment. Dependencies and migration head 0004 are unchanged.

## Checks and evidence

QA personally ran the original offline suite: 79 passed in 0.753 s. QA read root-assisted original integration output: 59 passed in 16.689 s. Earlier retained QA developer output shows 27 passed in 3.414 s. These passing suites did not cover the defect below.

Independent protocol run: four methods in 0.065 s; three passed, and the Retry-After method failed in all three whitespace subcases. Catalog projection/overflow, read-error cleanup and sanitized smoke output, and wrong-quantity smoke rejection passed. Its database HTTP-date restart/key-rotation case is reserved for root-assisted execution and is not claimed as passed here.

Evidence: [qa-unit-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w004-qa-2r5idwct/qa-unit-original-output.txt?type=file&root=%252F), [qa-protocol-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w004-qa-2r5idwct/qa-protocol-original-output.txt?type=file&root=%252F), [nutrition-w004-integration-final.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w004-integration-final.txt?type=file&root=%252F).

Probe: [qa_w004_independent.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w004-qa-2r5idwct/qa_w004_independent.py?type=file&root=%252F), SHA-256 594ce71f502d42211f98e87e069395582d1c48569c8caffc6434a5da468d31a1. Reproduce from its directory using the frozen interpreter, PYTHONDONTWRITEBYTECODE=1, W004_SOURCE_ROOT selecting the frozen source, and `-m unittest qa_w004_independent.ProtocolQA -v`.

A preliminary probe-authoring run compared schema export identification metadata as though it were a validation constraint. QA corrected that harness assertion to ignore export-only $id/$schema, then reran the original production source. The preliminary source/log remain separately preserved as authoring artifacts; that assertion was not a product defect. The final probe and original defect output above are the review evidence.

## Defect W004-QA-D01

Severity: medium; blocks A05's explicit requirement to respect valid Retry-After values and D012's one-day policy.

Reproduction uses the real standard-library HTTP header parser and a mocked HTTPS response, with no external connection. For HTTP 429, `Retry-After: 120 ` or `120\t` retains trailing optional whitespace in getheader(). Expected: retry delay 120 seconds. Actual: numeric parsing fails and the adapter falls back to 60 seconds, allowing an early retry. For `86401 `, expected: terminal ParserRejected because the hint exceeds one day. Actual: retryable ParserUnavailable with fallback 60 seconds. No hidden retry loop or food mutation was observed.

The lead accepted the finding and supplied a later fix. This original report does not claim the subsequent snapshot passes. Normalize surrounding HTTP SP/HTAB before interpreting the value, preserve size/type bounds, version the changed adapter policy, and recheck the unchanged probe against the separately identified source.

## Criterion assessment

| Criterion | Original assessment |
| --- | --- |
| A01 | Configuration shape/redaction and explicit model requirement pass; no dependency/migration changes. |
| A02 | Source and simulated protocol checks support fixed HTTPS/TLS defaults, request/schema bounds, no redirects/fallback and one request. Live compatibility unverified. |
| A03 | Independent catalog-instruction and private-key projection checks pass; overflow makes no request. |
| A04 | Strict schema/reference and envelope cases pass; independent response-read failure closes the connection and smoke output remains redacted. |
| A05 | Fails D01: HTTP optional whitespace can shorten a valid requested delay or bypass the terminal one-day limit. Other classification/bounded-retry checks pass. |
| A06 | Fingerprinting, key rotation, changed-model fencing and frozen-command recovery pass existing tests/source review. |
| A07 | Explicit CLI/smoke scope passes; independent wrong-quantity smoke case rejects without database access. |
| A08 | Exact source, independent failures and separate execution attribution recorded; live checks not asserted. |

## Coverage limits and next action

Synthetic transport only: no real provider request, key or selected model, language accuracy measurement, cost/latency result, or real Telegram activity. The prompt is not proof of complete injection resistance. Socket inactivity timeout is not an end-to-end deadline. No removed corpus was recreated.

Keep W004 in QA until a new snapshot passes the unchanged whitespace regression and relevant final suites. Preserve this report, probe and failed output; record a separate revision-specific recheck.
