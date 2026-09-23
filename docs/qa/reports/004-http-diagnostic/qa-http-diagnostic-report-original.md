# Independent QA — W004 HTTP diagnostic follow-up

Date: 2026-09-23. Reviewer: independent_m1_qa.
**Verdict: pass for the bounded diagnostic-only follow-up.** No defect found.

## Reviewed identity

Base: 7d561e03942c4fd5f559f8bf42f0c11ec36ca5d9.
Patch SHA-256: abb14015920b0bab1095ec152a03e274ea46961e2b06742546c43eea8afe700f.
Snapshot manifest: [review-manifest.json](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-http-status-review-4ki38q0u/review-manifest.json?type=file&root=%252F), SHA-256 eb6308a43ad135fdef305f1d15f48de96596acfb926a3857a4f73ceca253772a.
Reviewed runtime SHA-256: 6e330913787b613066370ee9d3bf61e6ea51999aa5b9a7d2e102956feb462b7f.
Reviewed regression-file SHA-256: 8dcf3d43b239d498eb69a8dac24d3c2003f4445cc5836008e56828591ff8b389.

QA verified all five manifest hashes and the patch digest, and compared every tracked snapshot file with its exact base blob. Only the five declared files differ, with no tracked file missing: one runtime line, one added CLI regression method, README, D012 and the W004 brief. Source hashes remain unchanged after checks. QA did not edit the shared project or frozen snapshot.

## Evidence and acceptance

| Acceptance | Independent evidence | Result |
| --- | --- | --- |
| Numeric rejection status is visible and smoke exits unsuccessfully | QA01 runs the real CLI with a simulated HTTP 401 response and asserts exact sanitized JSON, empty stderr and exit 1. Existing regression covers seven permanent/redirect statuses. | Pass |
| Provider body, reason, headers and secrets remain private | QA01 makes body reads and reason access raise immediately; neither occurs. Sensitive-shaped header/key markers are absent from stdout/stderr. The connection is requested/closed once and no database engine is created. QA02 rejects string, float, boolean, null and hostile integer-subclass statuses before interpolation. | Pass |
| Requests, fingerprint and retry classification are unchanged | QA03 loads the exact base adapter and compares request bytes and parser fingerprints using the same synthetic configuration. Error class and retry delay match across 13 permanent/transient statuses. Source review confirms only error text changed. | Pass |
| Database behavior remains unchanged | Tracked-file comparison shows no worker, service, migration or contract change; smoke probe asserts no database access. No DB rerun was needed or performed. | Pass by scope review |

QA personally ran three independent methods, all passed in 0.321 s, and the 15 existing Nebius protocol/CLI methods, all passed in 0.563 s. Logs: [qa-independent-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-http-status-qa-ox02_wsa/qa-independent-output.txt?type=file&root=%252F) and [qa-nebius-output.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-http-status-qa-ox02_wsa/qa-nebius-output.txt?type=file&root=%252F). QA separately read the lead's offline log reporting 82 passes in 0.849 s; that full-suite run was not personally executed by QA.

Probe: [qa_http_diagnostic.py](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-http-status-qa-ox02_wsa/qa_http_diagnostic.py?type=file&root=%252F), SHA-256 0fc0134e36770410da22677cbf6bad87998dc4c19cd9677dc7121ec99e3521e0.
Base comparison fixture: [baseline-nebius.py.txt](air-file://fai6b8iclscp0tss0s3r/private/tmp/nutrition-http-status-qa-ox02_wsa/baseline-nebius.py.txt?type=file&root=%252F), SHA-256 6b3f0b6985c43a2ed06b588a7019417a9422c2b789cb00e988b62ec16e6ca0ae. This is the exact base adapter obtained with git show; it is executed only with simulated transport.

Reproduce from the probe directory with the snapshot interpreter, PYTHONDONTWRITEBYTECODE=1 and HTTP_QA_SOURCE selecting the frozen snapshot: `-m unittest qa_http_diagnostic -v`. From the snapshot root: `-m unittest discover -s tests -p test_nebius.py -v`. Both use the existing Python 3.14.0 environment and no real credentials.

## Limits and closeout

No external request, actual provider response, real secret or database operation occurred. The change exposes a status; it does not diagnose the user's actual rejection or establish authentication, model availability, schema compatibility or language quality. Earlier W004 live-validation limits remain. The lead can close out this follow-up and preserve the reviewed patch identity alongside any later status/evidence packaging.
