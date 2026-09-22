# W003 independent QA — attempt 1

Date: 2026-09-22. Reviewer: separate independent QA agent, independent_m1_qa.
Verdict: **fail for the original snapshot**. Source-evidence validation can prepare incorrect food, quantity, basis, or date commands; valid dotted decimals can also be unnecessarily deferred. No live-model or external transport claim is made.

## Revision and evidence

Source ID: 3a0e362c8cadddc4e9a624d75e19f54956cd764409a29456a58eaf3f9efe5779.
Base commit: 46cdca0f4ce77d7cedfc513ac0ef1a581dc221d2. The source snapshot, rather than the base alone, identifies reviewed work.
Archive SHA-256: e706b7d2c18ee77ed792acabef3403f2fedfc19a314b2e83e90adc0d1dbf7262.
Manifest: [source-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-review-eez3dwmt/source-manifest.json?type=file&root=%252F).

QA verified all 96 manifest file hashes and the archive digest. Source hashes remained unchanged after checks. QA authored probes and reports outside the frozen source; no main-workspace source was edited.

Requirements read: constitution, W003 A01–A11, D010/D011, conversation contract, and QA strategy. Source review covered interpretation, orchestration, M1 preparation/execution integration, migration 0004, worker schema, CLI, and relevant tests. Expected probe outcomes were derived from source-evidence, dairy identity, lease, and recovery requirements, not copied from developer assertions.

Measured runtime: macOS 26.5.2 arm64, Python 3.14.0, SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg/psycopg-binary 3.3.6, Pydantic 2.13.5, jsonschema 4.26.0. The existing virtual environment was reused. PostgreSQL 17.11 is the supplied local environment; no live Telegram or Nebius calls were made.

| Check | Executor and actual result |
| --- | --- |
| Unit/contract/protocol/resolver discovery | QA: 64 passed in 0.261 s. |
| Integration discovery on the frozen source | Lead at QA request: supplied raw summary reports 53 passed in 14.565 s. QA inspected the suite source and summary. |
| Independent resolver evidence class | QA: six methods; five unsafe-input methods failed, with two failing range subcases; exact branded control passed. Six total failed assertions, 0.004 s. |
| Independent decimal evidence case | QA: both positive subcases failed, 0.002 s. |
| Three independently authored recovery checks | Requested through root assistance; their actual results belong in the later recheck report when available. No pass is asserted here. |
| Earlier retained QA suite | Developer reported 16 passes; independent rerun requested, not yet assessed in this report. |

Original raw evidence: [qa-resolver-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-resolver-original-output.txt?type=file&root=%252F), [qa-decimal-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-decimal-original-output.txt?type=file&root=%252F), [qa-integration-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-integration-original-output.txt?type=file&root=%252F).

Main independent probe [qa_w003_independent.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_independent.py?type=file&root=%252F), SHA-256 573fb5942f3c9355342a2f8e3e4f2dc23f1b74798bef8eacb5182353118cb357. Additional positive probe [qa_w003_decimal_evidence.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_decimal_evidence.py?type=file&root=%252F), SHA-256 d84d08a210019fe95c61c8eca09a1e5aba598b08ed04e12264035cb95edd16c1.

Reproduce from the probe directory using the frozen snapshot's interpreter, with W003_SOURCE_ROOT set to that source directory and PYTHONDONTWRITEBYTECODE=1. Execute `python -m unittest qa_w003_independent.ResolverEvidenceQA qa_w003_decimal_evidence -v`. Database-only reproduction is `python -m unittest qa_w003_independent.WorkerRecoveryQA -v`; it requires the local database and creates/removes only random nqa3 schemas.

## Findings

**W003-QA-D01 — high, product identity evidence can be bypassed.** Affects A02/A03/A11. Source “Съела 100 г творога” with the controlled proposal selecting an owned general “Хлеб” candidate becomes a ready bread command, bypassing dairy clarification. Source specifying творог 5% «Марка Б» also selects the sole 5% «Марка А» profile. Expected: unresolved when source identity conflicts or the material dairy detail remains unknown. Actual: ready command for the wrong product. QA01/QA02 reproduce this. Opaque owned candidate validity is necessary but does not establish a match to the food actually described.

**W003-QA-D02 — high, quantity ranges become exact quantities.** Affects A03. Both “80–100 г” and “80—100 г” are accepted as 100 g when the controlled proposal picks that endpoint. Expected: unresolved rather than an unapproved exact estimate. Actual: ready 100 g command. QA03 reproduces this.

**W003-QA-D03 — high, omitted unsupported relative dates silently default.** Affects A03/A07. A source ending “три дня назад”, with a null model date hint, resolves to the source day. Expected: unsupported date evidence remains unresolved with no reliable pending-food date. Actual: ready command dated 2026-09-22 in the fixture. QA04 reproduces this. The bounded resolver need not interpret every date expression, but it must not silently replace detected unsupported evidence with today.

**W003-QA-D04 — high, source preparation basis can conflict with selected profile.** Affects A03. Source “Съела 100 г вареной курицы”, an owned “Курица” raw profile, and a raw proposal produce a ready raw-basis command. Expected: unresolved; proposal/profile agreement cannot override explicitly cooked source evidence. QA05 reproduces this. No conversion engine is requested.

**W003-QA-D05 — medium, valid decimal evidence is mistaken for a date.** Affects A01/A03/A11. Exact matching sources containing “12.5 г” or a matching “5.5%” dairy profile become unresolved/date_unresolved. Expected: the supplied decimal quantity or fat percentage remains usable without a false date conflict. Both positive QA10 subcases reproduce this.

The lead accepted the findings for conservative resolver fixes. This report records the original failures; it does not claim those subsequent fixes were reviewed or that this snapshot passed.

## Criterion assessment

| Criterion | Original-snapshot assessment |
| --- | --- |
| A01 | Core known-food and synthetic reply path passes existing tests; dotted-decimal positive cases fail (D05). |
| A02 | Owned catalog construction, immutable version pinning and foreign references pass existing tests/source review; source/product identity match fails (D01). |
| A03 | Strict proposal shape, evidence excerpts and ordinary units pass existing tests; identity, quantity-range and basis conflict guards fail (D01/D02/D04), as do dotted-decimal positives (D05). |
| A04 | Existing controlled non-logging/multi-action dispositions and unsupported-action branches show no forced first action or food mutation. Passed within controlled-proposal scope. |
| A05 | Existing real process exits at claim/parse/preparation/domain boundaries and stable operation replay pass; additional independent frozen-command probe awaits root execution. |
| A06 | Existing competing/stale-claim, no-transaction parser call and bounded retry checks pass; source review found no additional concurrency defect. Independent stale-failure probe awaits root execution. |
| A07 | Existing captured date/midnight/DST and forwarded/reply checks pass; omitted unsupported relative-date evidence fails (D03). |
| A08 | Existing populated 0003 upgrade preserves applied/prepared work and owner constraints. Independent sent-receipt preservation probe awaits root execution. |
| A09 | CLI/status source review and existing error-redaction/fixture tests support scoped diagnostics and frozen context/schema/parser/resolver versions. Passed for synthetic operator commands. |
| A10 | Exact source, manifest and independent failures are recorded; live-model and real transport remain explicitly untested. Met as a review/evidence requirement. |
| A11 | Existing missing/conflicting dairy percentage guards and exact saved-profile cases pass, but general-candidate relabeling bypasses the rule and source/brand mismatch is accepted (D01); decimal percentage can falsely defer (D05). |

## Limits and next action

This is a review of a synthetic single-food worker, not general Russian intent accuracy. No interactive clarification, mixed-action execution, corrections, live model, live Telegram, real personal data, hosting, retention, or production operation was exercised. Developer tests are shared evidence rather than independent proof of language understanding. QA authored the additional cases and assessed failures independently; database execution requires root assistance and is attributed separately.

Keep W003 in QA. Apply the scoped evidence guards, preserve original source/probes/output, provide a newly hashed snapshot, recheck the unchanged probes and affected regressions, and record a separate revision-specific verdict. A resolver-version change should fence unfinished contexts when these resolution semantics change; already prepared commands should remain recoverable without another parse.
