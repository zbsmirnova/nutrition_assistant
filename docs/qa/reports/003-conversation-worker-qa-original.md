# QA report — W003 / attempt 3

## Identity and scope

Date: 2026-09-22. Reviewer: independent_m1_qa, separate independent QA agent.
Verdict: **pass for the frozen W003 synthetic single-food worker scope**. All eleven acceptance criteria have evidence; the five original defect groups, including the residual quantity-bound defect from attempt 2, are resolved. This is not a production or M2 completion verdict.

Source ID: 857b4097fc7f85b843bdc08169b5d61b9ecffa49f11fc98a554552252873d633.
Base commit: c45077a6e5706223f1aee7190d2d1b5cd739fc37.
Archive SHA-256: a37929ff642931d39826b32b4b67727adff4fb30526bdf77237ba8a05426fbd6.
Manifest: [source-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-review3-lrstedf7/source-manifest.json?type=file&root=%252F).

The explicit snapshot, not its base commit alone or the later lead workspace, identifies this review. QA verified all 99 manifest file hashes, archive digest, and the source-ID formula: SHA-256 of the UTF-8 compact sorted-key JSON representation of the ordered path/hash records; base_commit is excluded. A final hash recheck found no source changes. QA did not edit the frozen source or main workspace. The lead separately reported that all 50 runtime/migration/contract/dependency files in the main workspace still matched this snapshot. Later documentation, evidence packaging, and unrelated evaluation-corpus working-tree changes are outside this verdict.

Requirements reviewed: constitution, W003 A01–A11, D010/D011, conversation specification, QA strategy and development process. Review covered the resolver, worker claims/freezing/recovery, M1 service integration, migration 0004, scoped database constraints, CLI, and relevant test sources. The final delta from attempt 2 contains resolver v3's explicit quantity-bound guard, its developer regression, and four documentation files; worker, migration, service and transport behavior did not change. Resolver-version fencing makes unfinished incompatible contexts visible; prepared commands remain recoverable without another parse.

Runtime measured during this review: macOS 26.5.2 arm64; Python 3.14.0; SQLAlchemy 2.0.54; Alembic 1.20.0; psycopg and psycopg-binary 3.3.6; Pydantic 2.13.5; jsonschema 4.26.0. The existing virtual environment was reused. PostgreSQL 17.11 is the supplied local runtime, not a version independently queried by QA. Database checks use synthetic seeds and their own random schemas, with migration head 0004 and populated upgrade from 0003. No credentials are recorded here.

## Checks and evidence

QA independently designed expected outcomes from evidence, identity, ownership, recovery and migration requirements. Developer-authored tests provide shared regression evidence; they were not the sole basis for review. Database access required root assistance: the lead executed those commands, and QA inspected their source and actual output independently.

| Execution | Actual result | Executor and revision |
| --- | --- | --- |
| Default unit/contract/protocol/resolver/corpus discovery | 67 passed in 0.275 s | QA personally; attempt 3. |
| Original unchanged resolver, decimal and bound probes | Eight methods passed in 0.002 s | QA personally; attempt 3 selected through W003_SOURCE_ROOT. |
| Explicit PostgreSQL integration discovery | 53 passed in 14.273 s | Lead/root at QA request; frozen attempt 3. |
| Original unchanged worker recovery probes | Three passed in 0.645 s | Lead/root at QA request; attempt 3. |
| Retained QA discovery | 27 passed in 3.028 s | Lead/root; main workspace with matching production source and reviewed retention-only probe changes. Includes earlier 16 and these eleven W003 methods; this is a rerun, not 27 additional independent designs. |

Raw evidence: [qa-unit-attempt3-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-unit-attempt3-output.txt?type=file&root=%252F), [qa-resolver-attempt3-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-resolver-attempt3-output.txt?type=file&root=%252F), [nutrition-w003-integration-attempt3.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-integration-attempt3.txt?type=file&root=%252F), [qa-db-attempt3-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-db-attempt3-output.txt?type=file&root=%252F), and [nutrition-w003-retained-qa-final.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-retained-qa-final.txt?type=file&root=%252F).

Reproduction: from the frozen source, run its interpreter with `PYTHONDONTWRITEBYTECODE=1` and `-m unittest discover -s tests -v`, then `-m unittest discover -s tests/integration -v` with the documented local PostgreSQL configuration. From the QA probe directory, set W003_SOURCE_ROOT to the directory containing the reviewed manifest; use the same interpreter with `-m unittest qa_w003_independent.ResolverEvidenceQA qa_w003_decimal_evidence qa_w003_quantity_bound -v` and `-m unittest qa_w003_independent.WorkerRecoveryQA -v`. The retained packaging command is `-m unittest discover -s tests/qa -v` from the main project. The worker probes assert a local database host and create/remove only their own random schemas.

| Criterion | Independently assessed expectation and evidence | Status |
| --- | --- | --- |
| W003-A01 | Exact matching product/quantity stays supported, including 12.5 g. Integration independently expects 120 kcal, 16 g protein, 5 g fat, 3 g carbohydrate for its 100 g seed; one entry and response intent survive replay. Synthetic delivery renders entry and day totals. QA06/QA10 confirm positive resolution and pinned identity. | Passed |
| W003-A02 | Owned bounded catalog and strict candidate kinds/references prevent foreign or invented selection; execution rechecks authorization. Catalog mutation during parsing still uses the earlier immutable version. QA01/QA02 now reject relabeling dairy as bread and selecting the wrong explicit brand. | Passed |
| W003-A03 | Closed parser contracts and evidence validation reject malformed/out-of-context proposals before preparation. Units/basis and unknown-nutrient semantics retain earlier safeguards. QA03/QA05/QA10/QA11 verify ranges and bounds cannot become exact quantities, cooked source cannot use raw profile, and valid dotted decimals do not become dates. | Passed within the bounded supported input rules |
| W003-A04 | Controlled non-logging, unsupported and unresolved dispositions preserve plans/questions/product definitions/corrections/ambiguous food and multi-action inputs without choosing an arbitrary first action. Unit cases and worker tests show deferred work does not block later valid food or emit a false save acknowledgment. | Passed for controlled proposals |
| W003-A05 | Existing subprocess tests actually exit at claim, parse, preparation, and before/after domain commit, then recover without duplicate food/outbox. Stable operation identity preserves retries while distinct source messages stay distinct. Independent QA08 resumes an already frozen command using a different adapter without invoking it. | Passed |
| W003-A06 | Database-time leases and claim-token fencing prevent competing or stale workers replacing a winner. Parser runs outside database transactions; bounded failure retries terminate visibly and do not block other inputs. Independent QA07 pauses a failing old parser, installs a newer non-logging winner, then proves the stale failure returns lost_claim without overwriting it. | Passed |
| W003-A07 | Captured timestamp/time zone drives delayed, midnight and DST dates. Unsupported relative evidence cannot silently default to today; QA04 also checks there is no invented reliable pending date. Reply/forward inputs defer without a parser call. | Passed |
| W003-A08 | Populated 0003-to-0004 checks preserve accepted sources, prepared/applied commands, entries and scoped constraints. Independent QA09 also preserves a sent receipt, attempt count and immutable outcome, and resumes pending work without parsing or duplicating the prior entry. | Passed |
| W003-A09 | CLI/status and fixture paths expose durable progress without provider credentials. Existing failure tests verify diagnostic redaction and frozen context/parser/schema/resolver versions; retry version mismatch is explicit. Frozen prepared work remains usable with a later adapter. | Passed for synthetic operator commands |
| W003-A10 | Exact revisions, archived failures, unchanged original probes, test attribution and version-specific rechecks are recorded. The two corpus checks validate authored data integrity only. No live-model or real-transport result is asserted. | Passed |
| W003-A11 | Missing/conflicting material dairy fat stays unresolved with no food/outbox; known-date pending food appears in later totals. QA01/QA02 close identity bypasses; QA06/QA10 preserve exact branded and matching decimal-percentage positives. Unit cases show percentage alone does not supply grams or model-generated nutrition. | Passed |

## Defects and rechecks

The original failed reports remain unchanged: [qa-w003-attempt1-report.md](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-w003-attempt1-report.md?type=file&root=%252F), SHA-256 4d19e8a6c9adbe267de231450947d188dd9b22962526340907d6684a6a1dd15f; [qa-w003-attempt2-report.md](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-w003-attempt2-report.md?type=file&root=%252F), SHA-256 ca81e9e2c4468be46c5807d231a2b9430612494055c4b932a1e187c1fc183385. They retain exact failed source identities, reproductions and expected/actual outcomes.

| Finding | Prior failure and expected behavior | Final disposition |
| --- | --- | --- |
| D01, high | Dairy source relabeled as general bread; explicit other brand accepted. Conflicting source/product identity must defer. | Resolved by identity evidence checks; QA01/QA02 pass unchanged. |
| D02, high | En/em-dash range became exact 100 g. Attempt 2 fixed those cases but still accepted “до 100 г” as exact. Bounds/ranges must defer without an approved estimate. | Resolved by resolver v3 bound-prefix rejection; original range and subsequent bound probes both pass unchanged. |
| D03, high | Omitted “три дня назад” hint silently defaulted to source day. Unsupported source date evidence must defer without a fabricated pending date. | Resolved; QA04 passes unchanged. |
| D04, high | Explicit cooked source became a raw-profile command. Source/profile basis conflict must defer. | Resolved; QA05 passes unchanged. |
| D05, medium | Valid 12.5 g or matching 5.5% was mistaken for a short date. Exact supported decimal evidence must remain usable. | Resolved by excluding quantity/percentage spans from short-date detection; both QA10 subcases pass unchanged. |

Historical results remain attached to their sources: original 64 unit checks passed, but independent resolver/decimal cases failed; root-assisted original integration had 53 passes, earlier retained probes 16 passes in 2.816 s and independent recovery probes three passes in 0.660 s. QA subsequently assessed those original recovery/retained outputs. Attempt 2 had 66 passing unit checks and seven passing original resolver methods, but the new bound probe failed; its separately read integration log reports 53 passes in 14.289 s. These historical passes are not substituted for the final runs above.

## Probe identity and retention

| Original independently authored artifact | SHA-256 |
| --- | --- |
| [qa_w003_independent.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_independent.py?type=file&root=%252F) | 573fb5942f3c9355342a2f8e3e4f2dc23f1b74798bef8eacb5182353118cb357 |
| [qa_w003_decimal_evidence.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_decimal_evidence.py?type=file&root=%252F) | d84d08a210019fe95c61c8eca09a1e5aba598b08ed04e12264035cb95edd16c1 |
| [qa_w003_quantity_bound.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_quantity_bound.py?type=file&root=%252F) | 4c86db4bec1d5317f67ef34d5b02881dc411297efa5e83b6b27e3331b2a389c2 |

All three originals are unchanged. QA compared the retained copies byte by byte: only scratch source-path injection is removed from the main probe, and the two helper imports change to the retained module name. No assertion, fixture, query or expected outcome changes. Approved retained hashes:

| Retained artifact | SHA-256 |
| --- | --- |
| [test_w003_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w003_independent.py?type=file&root=%252F) | a4d4fd8a56dd376b41a8a2ec9033399da8324541214b11a2b81fbd1101b3b919 |
| [test_w003_decimal_evidence.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w003_decimal_evidence.py?type=file&root=%252F) | 8c9db17f8ad6c4faa5ad9102d7a4ac1025153cfe25f7fcc26fff3cea01f7715c |
| [test_w003_quantity_bound.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w003_quantity_bound.py?type=file&root=%252F) | 46d96fa784fce9dc9c9cd534943c36a82971274a2a1c5789f752cd4d306542e2 |

## Coverage limits and verdict

No live Nebius/model call, real Telegram send, real personal data, general Russian-language accuracy evaluation, interactive clarification, mixed-action execution, correction workflow, deployment, backup/restore, retention or production operation was exercised. The authored 50-case corpus and its two integrity checks do not establish model accuracy; their presence explains the frozen default-suite count. Supported resolution remains conservative and bounded, rather than a claim that all natural-language phrasing is understood. Outbox recovery does not establish exactly-once visible Telegram delivery.

**Pass for attempt 3 and W003 A01–A11 within the stated synthetic scope.** No unresolved blocking or additional nonblocking defect remains from this review. The lead may complete W003's documentation/evidence closeout and authorized commit workflow, preserving the exact reviewed source identity and marking later packaging changes separately. M2 and personal-release readiness require their remaining slices and evidence.
