# Independent QA — W004 smoke expectation follow-up

Date: 2026-09-23. Reviewer: independent_m1_qa.
**Verdict: pass for the bounded smoke comparison and diagnostic change.** No blocking or additional nonblocking finding remains. The specific cause of the user's live mismatch is still unknown.

## Reviewed identity

Base: 2ebabbb805f095a05f8112865168decf18123dfc.
Patch SHA-256: 044191e834cb2bc18a765b5ae187fba0982f239e7504268fd4b0a794058c2f02.
[review-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-smoke-review-clgupvep/review-manifest.json?type=file&root=%252F) SHA-256: 49722cb07d4537cc981f752317b7d1aec4cb79449cbfe32d96c2659adaceed22.
Runtime SHA-256: 0821ba445f9fe31e539dddf9119a2e9cbb901535e8aab859bdc2c0586905bcbc.
Test-file SHA-256: 4c9545c8e525aa3ba59cfd858365153e54ada14181bd260954861adc37d745a0.

QA verified the patch and all seven manifest hashes, and compared every tracked snapshot file to its exact base blob. Only the seven declared files differ; none are missing. Runtime changes are confined to the smoke helper and its Decimal import. Prompt, request construction, local resolver, parser fingerprint logic, worker, contracts and migrations are unchanged. Final hashes remain identical. QA edited only its own scratch directory.

## Acceptance and evidence

| Acceptance | Independent assessment | Result |
| --- | --- | --- |
| Equivalent representations of 100 g pass | QA01 executes the exact base and corrected helpers: canonical 100 passes both; 100.0, 100.00 and 100.000000 are falsely rejected by the base and accepted after the fix. | Pass |
| Incorrect, unresolved and unsupported actions still fail | QA02 rejects 99, 100.000001 and 101; unresolved quantity; all four non-logging reasons; and a schema-valid 32-action proposal. Existing tests also reject missing basis/quantity, unresolvable food and date. | Pass |
| Diagnostic confidentiality and boundedness | QA03 exercises the real CLI with injected provider responses. Arbitrary unresolved paths map to other; a known quantity.amount path remains useful. Private markers in paths, food names, date text and response metadata do not appear in stdout/stderr; neither do credentials or source/product text. One versus 300 distinct private paths emits the same-size diagnostic. Each tested output is under 500 characters; stderr is empty. | Pass |
| No database access or extra request | Independent CLI cases assert no engine creation, one provider callback and unsuccessful exit. | Pass |
| Provider request and interpretation identity unchanged | QA01 compares actual request bytes and parser fingerprints before/after for all decimal cases; both are identical. Source comparison confirms no worker or parsing change. | Pass |

The diagnostic's possible action kinds are validated schema literals. Source review confirms resolver status/reason values come from local constants or the NonLogging reason literal; free-form proposal text is not interpolated. Unresolved-field output is a deduplicated finite whitelist plus other, so arbitrary path count/length cannot make the diagnostic grow. This conclusion is supported by source constraints as well as the stress probe.

QA personally ran three independent methods, passed in 0.217 s, and all 18 existing Nebius protocol/CLI methods, passed in 0.767 s. Raw logs: [qa-independent-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-smoke-qa-4uo2__3a/qa-independent-output.txt?type=file&root=%252F) and [qa-nebius-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-smoke-qa-4uo2__3a/qa-nebius-output.txt?type=file&root=%252F).

QA separately assessed the lead's preserved output: the expected pre-fix run had three errors among 17 methods; the final offline run passed 85 in 1.014 s. The first retained run had two database permission errors and is not counted as a pass. The approved rerun passed five retained W004 checks in 0.376 s. These were lead executions; QA did not execute a DB suite. The existing Python 3.14.0 environment was reused with no dependency/migration changes.

## Reproduction artifacts

[qa_smoke_expectation.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-smoke-qa-4uo2__3a/qa_smoke_expectation.py?type=file&root=%252F) SHA-256: d703a0961dda0f9dc14a6838fa15eec4af30e32ccecf185a544218746040cf1c.
Its same-directory [baseline-nebius.py.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-smoke-qa-4uo2__3a/baseline-nebius.py.txt?type=file&root=%252F) is the exact base adapter, SHA-256 1d7ef8243cd38aefeb715b9a2342c51123952e751f4ab889cfab5d637e1ef67c.

From that directory, use the snapshot interpreter with PYTHONDONTWRITEBYTECODE=1 and SMOKE_QA_SOURCE selecting the frozen source: `-m unittest qa_smoke_expectation -v`. From the snapshot root, run `-m unittest discover -s tests -p test_nebius.py -v`. All personally executed tests are offline, with synthetic configuration and injected responses.

## Limits and closeout

No live provider request, real secret, database operation or user proposal was available to this review. The before/after probe proves a definite numeric-representation bug in the smoke harness; it does not establish that this was the user's actual failure. The user's prior message supports only that envelope/schema/reference validation reached the expectation check. A terminal rerun is still needed to observe the specific mismatch or successful smoke result. No model-quality, cost/latency or production-readiness claim is made.

The lead may close out the follow-up and retain this exact source identity with later documentation/evidence packaging attributed separately.
