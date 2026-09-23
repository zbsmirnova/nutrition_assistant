# Independent QA — W004 schema-wrapper correction

Date: 2026-09-23. Reviewer: independent_m1_qa.
**Verdict: pass for the bounded request-wrapper correction.** The legacy payload fails the published contract and the corrected payload passes. Live model compatibility remains unverified.

## Exact review identity

Base: 86a77da4fd1c2426202228d876c9b1b457d90a84.
Patch SHA-256: 159edbfb057663188e179aaaa2c3f3c30038a35ea43c9cd73f27072620a7f83e.
[review-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/review-manifest.json?type=file&root=%252F) SHA-256: f21c2c5d46f7575ed906ca32e8b5f756c859368fcf248ddfeaf493d711aa3f57.
Runtime SHA-256: 1d7ef8243cd38aefeb715b9a2342c51123952e751f4ab889cfab5d637e1ef67c.
Provider-fixture SHA-256: b0fa76e23eea84d637f2a367d48cf1f51fc7f93cddde0adb95f071a9ba38db63.

QA verified all eight manifest hashes and the patch digest. Comparison with exact base blobs found the seven declared changed tracked files and no missing tracked file; the provider fixture is the declared addition. No other runtime, prompt, contract, migration or worker change is present. Final source hash recheck was clean. QA edited only its scratch artifacts.

## Provider evidence and acceptance

QA checked the supplied full OpenAPI download, version 20260916-b712a99a4, SHA-256 e6ba0e6dc303e48fb8eec5d62fcc29cfc2f552a7725a2ae0903719023961ddb5. Both extracted fixture definitions equal the full source exactly. QA traced the actual /v1/chat/completions request schema through ChatCompletionRequest to the same ResponseFormat component, then validated complete generated request payloads against the full downloaded contract. The source identifies [Nebius OpenAPI](https://api.tokenfactory.nebius.com/openapi.json); QA used the attributed downloaded bytes without another network fetch.

| Follow-up criterion | Independent assessment | Result |
| --- | --- | --- |
| 1. Provider-contract failure before, pass after | Exact base adapter payload lacks wrapper name/schema and fails full published request validation. Corrected payload validates; extracted fixture and provenance match the full source. The wrapper has the chosen name and strict=true. | Pass |
| 2. Inner schema, prompt, privacy, local validation and limits preserved | Independent before/after comparison proves inner schema equality and equality of every other outgoing request field, including messages and policy. Private owner/version/observation sentinel fields remain excluded. Both implementations accept the same valid response and reject a foreign candidate. Existing protocol checks cover redaction, malformed output, TLS construction, redirects and size limits. | Pass |
| 3. Identity changes, key rotation and recovery remain correct | New fingerprint differs from the base; rotating only the key changes neither fingerprint nor payload. Source hashes the actual wrapper and bumps adapter version to v3. Lead-executed provider-worker tests preserve bounded retries, key rotation, unfinished-work fencing and prepared-command recovery without another provider request. | Pass |
| 4. Regressions and exact independent evidence; live limits explicit | Personally executed checks below pass; lead's targeted DB and full offline evidence were separately assessed. No real provider call, user key or live Qwen response was available to this review. | Pass within scope |

## Execution and evidence

QA personally ran three independent probes, passed in 0.116 s; all 16 existing Nebius protocol/CLI tests, passed in 0.601 s; and the four retained W004 protocol probes, passed in 0.066 s. Raw logs: [qa-independent-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/qa-independent-output.txt?type=file&root=%252F), [qa-nebius-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/qa-nebius-output.txt?type=file&root=%252F), [qa-retained-protocol-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/qa-retained-protocol-output.txt?type=file&root=%252F).

QA read the lead's raw results: 83 offline tests passed in 0.906 s; six provider-worker DB tests passed in 1.302 s; five retained W004 checks passed in 0.439 s. QA also inspected the preserved pre-fix run summary: one error among 16 methods. The independent before/after probe provides separate confirmation of the contract mismatch. Database execution was performed by the lead, not QA. Existing Python 3.14.0/dependency environment was reused; no dependency or migration change.

Probe [qa_wrapper.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/qa_wrapper.py?type=file&root=%252F), SHA-256 1ee82a298529ca3d6587a658381dd9a7060265a526c43061aa524a32b63dfa8c. Its same-directory dependencies are [baseline-nebius.py.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/baseline-nebius.py.txt?type=file&root=%252F), the exact base adapter with SHA-256 6e330913787b613066370ee9d3bf61e6ea51999aa5b9a7d2e102956feb462b7f, and [provider-openapi.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-schema-wrapper/provider-openapi.json?type=file&root=%252F), matching the full-source hash above.

Reproduce from the probe directory with the snapshot interpreter, PYTHONDONTWRITEBYTECODE=1 and WRAPPER_QA_SOURCE selecting the frozen source: `-m unittest qa_wrapper -v`. Existing protocol command from snapshot root: `-m unittest discover -s tests -p test_nebius.py -v`. With PYTHONPATH set to the snapshot tests/qa directory, run `-m unittest test_w004_independent.ProtocolQA -v` for the retained offline subset. No live credentials/network/database are needed for these commands.

## Retained assertion approval and disposition

QA explicitly approves the retained W004 adaptation: the only change is selecting response_format.json_schema.schema instead of response_format.json_schema before comparing the complete inner schema with the generated export. No expected constraint is removed or relaxed. Previous retained SHA-256 d5cc683d759e6a432ef34070e75c9930934cca7d09df7f8f891db4eee022bca2; adapted SHA-256 25502cb228a0a59b385ca1f2fa792d6832f17abb5fc63ee6fe88228a91b2c2b8. The original sources/reports remain historical evidence. Earlier protocol QA mirrored the documented direct-schema example and did not catch this provider-contract mismatch; it is not retrospective live-compatibility evidence.

No blocking implementation finding remains. One nonblocking wording clarification is agreed for closeout: the provider requires name and schema; strict is optional in OpenAPI and explicitly enabled by this adapter. The lead will clarify README wording without changing reviewed runtime.

No successful real inference, language accuracy, model-specific strict-schema support, latency or cost was measured. User-reported HTTP 422 is consistent with the proven request-shape mismatch, but this offline review does not establish that the wrapper is the only remaining live issue. The lead may close out the correction and retain this exact review identity; a user-terminal smoke rerun remains necessary to observe live behavior.

Retention note by lead: artifact links point to committed copies; the original report is retained verbatim beside this copy. After review, README wording now distinguishes required name/schema from optional strict mode, and the work brief records historical setup attempts and closes this follow-up. Runtime, test and provider-fixture bytes remain unchanged.
