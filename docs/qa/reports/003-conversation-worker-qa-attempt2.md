# W003 independent QA — attempt 2

Date: 2026-09-22. Reviewer: independent_m1_qa.
Verdict: **fail for attempt 2: one residual quantity-evidence defect remains**. The five original defect groups otherwise pass their unchanged independent reproductions. This report supplements, and does not modify, the original failed report.

## Revision and review

Source ID: effdac279ab123929d2e10076dc5dea44018112a55c50eeb431ed272d63b1801.
Base commit: c45077a6e5706223f1aee7190d2d1b5cd739fc37.
Archive SHA-256: 614a866e0e16d96fd759f2322a6261d8a520f927ae9d0ba57f38fc987da2cc58.
Manifest: [source-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-review2-elk56ot8/source-manifest.json?type=file&root=%252F).

QA verified all 99 source file hashes and the archive digest, and independently recomputed the source ID as SHA-256 of compact sorted-key JSON encoding the ordered path/hash file records. The same formula independently verifies the original source ID. The changed base commit contains a separately added evaluation corpus; its two integrity tests explain the default-suite increase from 64 to 66. They do not measure model accuracy.

Only the interpretation module changes runtime behavior from attempt 1: resolver v2 checks source catalog-name evidence, explicit raw/cooked contradictions, quantity range/approximation evidence, and unsupported relative-date markers; decimal quantity/percentage spans are excluded from date detection. QA read this delta, its specification update, changed test assertion, and relevant setup/brief changes. The version bump correctly makes unfinished resolver-v1 contexts fail visibly rather than silently changing semantics. Already prepared commands remain recoverable.

## Executed evidence

| Check | Actual result and attribution |
| --- | --- |
| Default unit discovery on attempt 2 | QA personally ran 66 tests; passed in 0.259 s. |
| Unchanged independent resolver and decimal probes on attempt 2 | QA personally ran seven methods; all passed in 0.002 s. This resolves the originally reproduced cases for D01–D05. |
| Additional upper-bound probe on attempt 2 | QA personally ran one method; failed in 0.001 s. |
| Original retained earlier-slice QA rerun | Lead at QA request; raw summary reports 16 passed in 2.816 s. QA assessed this newly available output. |
| Original independent recovery probes | Lead at QA request; all three passed in 0.660 s. QA read their output: stale failure cannot overwrite a newer terminal result; frozen commands resume with a different adapter without parsing; populated migration preserves sent receipt and prepared work. These results apply to original source. |

New raw outputs: [qa-resolver-recheck-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-resolver-recheck-output.txt?type=file&root=%252F), [qa-bound-attempt2-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-bound-attempt2-output.txt?type=file&root=%252F), [qa-retained-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-retained-original-output.txt?type=file&root=%252F), and [qa-db-original-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa-db-original-output.txt?type=file&root=%252F).

The original probe hashes remain unchanged: 573fb5942f3c9355342a2f8e3e4f2dc23f1b74798bef8eacb5182353118cb357 and d84d08a210019fe95c61c8eca09a1e5aba598b08ed04e12264035cb95edd16c1. Their bootstrap selects the reviewed source through W003_SOURCE_ROOT; no production source is edited to run them.

## Residual W003-QA-D02

Severity: high for the exact-quantity requirement A03. Source “Съела до 100 г творога 5% «Марка А»”, with a controlled 100 g proposal and matching catalog profile, still resolves ready with an exact 100 g command. The new range guard requires a preceding number before “до”, so it catches “80 до 100” but misses an independent upper bound.

Expected: unresolved, no command, because an upper bound does not establish the eaten quantity and no estimate was approved. Actual: ready command. This is a residual of the original quantity-evidence defect, not a request for a general language parser or estimation engine.

Reproduction: run `python -m unittest qa_w003_quantity_bound -v` from the QA probe directory using the snapshot interpreter and W003_SOURCE_ROOT for attempt 2. Probe [qa_w003_quantity_bound.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-w003-qa-eo35kq3z/qa_w003_quantity_bound.py?type=file&root=%252F), SHA-256 4c86db4bec1d5317f67ef34d5b02881dc411297efa5e83b6b27e3331b2a389c2. Original probes and reports remain intact.

## Criterion disposition and next step

A01, A02, A07, and A11 now pass their targeted resolver rechecks. A03 remains failing because of the upper-bound case; its originally reported identity/range/basis/decimal cases pass. A04/A05/A06/A08/A09 retain the original source-review and baseline evidence, augmented by the three passing original recovery probes. Any new database runs on attempt 2 must be recorded separately rather than relabeled from original results. A10 is met by exact source identification, preserved failures and independent rechecks.

The review remains synthetic: no live Nebius/Telegram call, interactive clarification, mixed-message execution, correction workflow, or general Russian accuracy claim. Runtime/dependency and executor limitations remain as recorded in the original report. The two new corpus integrity tests establish only authored data structure.

Apply a conservative guard for standalone quantity bounds, provide the next exact snapshot, and rerun the unchanged probes plus the upper-bound regression. W003 should remain in QA until that targeted defect is resolved and final regression evidence is assessed.
