# W004 — Connect the conversation worker to Nebius

Status: done.
Milestone: M2 (provider transport slice; does not complete M2).
Owner: lead assistant, architect/developer; existing independent reviewer for QA.
Updated: 2026-09-23.

## Outcome and scope

Implement the selected Nebius Token Factory provider behind W003's Parser interface. An explicit operator command can interpret one identified inbox source; a separate fixed synthetic smoke check verifies the configured model's response without database writes. Environment configuration alone never starts requests or processes the inbox.

This slice verifies API transport, request construction, local response validation, and worker recovery with injected responses. A live smoke check requires the user-supplied secret and an explicit model. General Russian-language evaluation, model selection, clarification questions/answers, corrections, and real-data retention remain later work. Do not recreate the separately removed evaluation corpus.

## Requirements and decisions

CALC-001, FOOD-001/002/005, DATA-002/003; D009 provider/secret contract, D010 dairy identity, D011 worker recovery. D012 records concrete provider transport and versioning. Q09 retains model/quality evaluation; Q10 retains real-data lifecycle choices. Neither blocks synthetic adapter implementation.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W004-A01 | Configuration requires NEBIUS_API_KEY and an explicit NUTRITION_LLM_MODEL; missing/invalid values fail without echoing values or making requests. No new dependencies or migration are necessary. |
| W004-A02 | Requests use the documented fixed HTTPS endpoint, bearer authentication, verified TLS, bounded timeouts and sizes, one non-streaming completion, and the existing generated ParserOutput schema. Redirects and provider/schema fallback are never followed. |
| W004-A03 | Provider context contains only source text/date/time zone and bounded public product fields/tokens. Application/Telegram IDs, unrelated observations, and full history are not sent. Source/catalog text is treated as data in a versioned system prompt. |
| W004-A04 | Only a complete single assistant response with content can reach local schema/reference validation. Refusal, truncation, tool calls, malformed/oversized response and invalid JSON produce no food or false success. Diagnostics omit keys, payloads and provider exception details. |
| W004-A05 | Transient transport/408/429/5xx failures use durable bounded worker retries; valid Retry-After delays are respected. Permanent HTTP failures and invalid completion envelopes stop visibly. No hidden retry loop, model switch, schema downgrade or JSON repair occurs. |
| W004-A06 | Parser identity includes model, prompt, schema and request policy, but not the secret. Credential rotation preserves identity; changed interpretation settings fence unfinished work. Prepared/applied commands resume without another model call or duplicate write. |
| W004-A07 | Explicit worker CLI and fixed synthetic smoke CLI are documented and tested without real credentials. Smoke validates the expected action through the resolver without database access; worker still uses M1 authorization/arithmetic and D010 deferral. |
| W004-A08 | Relevant regressions and independent review identify an exact source. Live compatibility, model accuracy, latency/cost and real Telegram remain explicitly unverified unless separately observed. |

## Implementation checklist

- [x] Bound the slice and verify official provider documentation.
- [x] Implement versioned prompt, configuration, HTTPS adapter and response policy.
- [x] Connect explicit worker/smoke commands and durable retry classification.
- [x] Run protocol/CLI and PostgreSQL regressions; maintain affected docs.
- [x] Obtain independent review, address findings and retain evidence; close out through the authorized local commit workflow.

## Developer handoff and QA

Baseline: 7bea583 (W003 implementation e02934e plus separately committed IDE files). Prior project checks: 65 offline, 53 integration, 27 retained QA. Final verification: 79 offline, 59 integration and 32 retained QA checks pass. Independent review passed all eight criteria on the corrected snapshot. The first offline run exposed a missing synthetic context revision in the smoke helper, which was fixed before the passing rerun. Completion requires its eight criteria, relevant passing regressions, independent source-specific review, maintained docs and the authorized local commit. No live requests had run at slice completion.

Final reviewed source: d31d4079dfe8ecf0cae2309ad734f1bcf5d347cc31b37294811d7fd1d1492087. QA found one blocking retry-header whitespace defect, fixed and rechecked unchanged; original evidence is preserved. [004-nebius-adapter-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-developer.md?type=file&root=%252F) records developer/root-assisted execution. [004-nebius-adapter-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa.md?type=file&root=%252F) records independent assessment and the exact source. Later documentation/evidence packaging is recorded separately in the closeout manifest.

W004 is complete for provider protocol and worker integration. No live model has been selected or called. The next dependent step is the explicit synthetic smoke check after configuration, followed by measured model evaluation. Clarification/resumption remains a subsequent M2 implementation slice and can proceed synthetically before the key is available.

## Setup follow-up — 2026-09-23

The user reported `parser_unavailable` / `Nebius request unavailable` while setting up the synthetic smoke check with Qwen/Qwen3-30B-A3B-Instruct-2507 as a candidate. On revision 715b20d128abc7ef8e179e581bba1aebae07f973 (application runtime unchanged from W004's a2eb614), a developer probe using the project's Python 3.14.0 reproduced certificate verification failure (code 20, unable to get local issuer certificate); the default CA file was missing. A sandboxed probe first encountered DNS restrictions; the certificate failure and successful recheck were observed with network access approved.

Setting SSL_CERT_FILE to the existing /etc/ssl/cert.pem allowed the same interpreter's default HTTPS connection to GET /v1/models to return HTTP 401 without authentication. No key, source text, inference request, or database access was used by these probes. This verifies the local TLS setup fix, not authentication, model availability, or successful inference. The user must retry the smoke command in the terminal holding their environment variables. Setup instructions are maintained in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F).

Only documentation changed. Validation for this follow-up covers the observed connection failure/recheck, affected document links and formatting; no new independent QA or application regression run is claimed. The original implementation review above remains scoped to its recorded source.

## HTTP diagnostic follow-up — 2026-09-23

Status: done for the diagnostic change; authentication setup remains pending. The next user smoke attempt reached a permanent HTTP rejection, but the existing message hid the status. The error now exposes only the integer status; credentials, response bodies, headers and reason phrases stay out of diagnostics. The user subsequently reported HTTP 401 from the updated smoke command. This identifies an authentication rejection, without establishing why the credential was rejected or whether the model/schema is compatible. The next action is to re-enter a complete Token Factory secret key in the user's terminal and retry; no credential was inspected by the assistant.

Acceptance: the smoke CLI prints the rejection's numeric HTTP status and exits unsuccessfully; error bodies remain unread and no sensitive data appears in stdout/stderr; requests, parser identity, retry classification and database behavior remain unchanged. Validate with offline protocol/CLI regressions and independent review of an identified source before committing. No live call or database test is needed for a diagnostic-text change.

Verification: 82 developer offline tests pass; independent QA passes three additional probes and all 15 Nebius protocol/CLI tests, with no defect found. [qa-http-diagnostic-report.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-http-diagnostic/qa-http-diagnostic-report.md?type=file&root=%252F) identifies the base, reviewed patch and exact source hashes, and links the retained evidence. The reproducible [004-http-diagnostic-source.patch](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-http-diagnostic-source.patch?type=file&root=%252F) applies to 7d561e03942c4fd5f559f8bf42f0c11ec36ca5d9. [004-http-diagnostic-developer-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-http-diagnostic-developer-output.txt?type=file&root=%252F) preserves the full offline run. Final packaging only adds evidence, closes this status and clarifies README wording; runtime and tests match the reviewed hashes.
