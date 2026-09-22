# W004 developer handoff — Nebius adapter

Recorded: 2026-09-22. Executor: lead assistant, developer role.

## Exact source and scope

Source 3b4ee706e7d0fab4b917d9711c2355da08cba8a3d6f2eb89c56ec64f15fdb205; base 7bea583d1f567e0971d48993bccfc59b35d8a5ae; 105 files. [004-source-manifest-attempt1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-source-manifest-attempt1.json?type=file&root=%252F) records every file and archive identity. Source identity excludes reports/evidence, IDE files, secrets, environment and Git metadata. Archive SHA-256: 078fc093b2ecb4ec0c2cd97bff78452b2fa553258298ffcba004985ef3bb7eb9.

Adds fixed-origin verified HTTPS, environment configuration, direct generated-schema requests, a versioned prompt, minimal public context, strict completion/schema/reference validation, bounded and sanitized failures, durable Retry-After handling, parser fingerprints, and explicit worker/synthetic-smoke commands. No dependency, migration or portable-contract changes. D012 records choices and limits; W004 A01–A08 own acceptance.

## Developer checks

| Execution | Observed result | Raw output |
| --- | --- | --- |
| Default discovery | 79 passed, 0.961 s | [004-developer-unit-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-unit-output.txt?type=file&root=%252F) |
| PostgreSQL integration | 59 passed, 16.510 s | [004-developer-integration-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-integration-output.txt?type=file&root=%252F) |
| Retained QA | 27 passed, 3.414 s | [004-developer-retained-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-retained-output.txt?type=file&root=%252F) |
| Formatting | git diff --check passed at handoff | Tool output |

The first offline execution had 77 passes and one smoke-helper error: missing context_revision. Adding its fixed synthetic revision resolved it; a further explicit worker-CLI check brought the passing offline count to 79. Preserve [004-developer-unit-original-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-unit-original-output.txt?type=file&root=%252F). The initial integration run preceded that smoke-only fix; a final exact-snapshot integration run follows for independent review. Retained checks ran after the fix. Database access required escalation to the local disposable-schema PostgreSQL instance; no provider/Telegram requests occurred. Runtime/dependencies remain the established Python 3.14/PostgreSQL17 project environment.

## Limits and independent review

This is developer verification, not an independent verdict. The existing independent reviewer receives the frozen source, acceptance criteria and exact evidence. Source-specific findings and rechecks will be retained separately.

The default endpoint uses the official Nebius direct json_schema request format, verified from documentation fetched on 2026-09-22. Those examples have formatting inconsistencies; actual model/schema compatibility still needs a live smoke request. The key has not been inspected; no model is selected, no live inference or Telegram check has run, and language quality, latency/cost and immutable provider model revision remain unverified. The 30-second timeout bounds socket inactivity, not total wall time. No JSON repair, provider/model fallback or auto schema downgrade is implemented. Q10 and later M2 flows remain open. The separately removed evaluation corpus is not recreated.

Final frozen-source integration rerun: 59 passed in 16.689 s, exit 0; retained in [004-developer-integration-final-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-integration-final-output.txt?type=file&root=%252F). Dependency check passed. All 300 Air file links across 40 Markdown documents existed at handoff.

## Attempt 2

Independent QA found that valid Retry-After values with trailing HTTP whitespace fell back to a shorter delay; whitespace could also bypass the one-day limit. The adapter now strips surrounding SP/HTAB before parsing. Date delays use ceiling rather than an unconditional extra second, preserving the exact one-day boundary. The adapter policy marker is v2 so unfinished work cannot silently switch interpretation policy. Developer regression cases cover whitespace and the exact date boundary. Original source and evidence are retained.

New source d31d4079dfe8ecf0cae2309ad734f1bcf5d347cc31b37294811d7fd1d1492087; archive SHA-256 e2a4c3047e88267d1322b1693226de1c1e02dd35c4de2f5c8264a4d97841f124; same base and 105 files. [004-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-source-manifest.json?type=file&root=%252F) identifies the corrected review snapshot. Final rechecks follow on this exact source.

Attempt-2 developer rechecks: 79 offline checks and 59 integration checks (15.480 s) passed on the frozen source. The unchanged independent HTTP-date recovery probe passed in a root-assisted run (1 test, 0.337 s). The final retained suite passed 32 tests after copying five independent W004 probes with only source-bootstrap removal. All 68 reviewed runtime/prompt/test/contract/dependency/migration files still match the snapshot. These executions are developer/root-assisted evidence, distinct from QA’s own executions and verdict.

Final independent result: all eight scoped criteria passed on attempt 2; see [004-nebius-adapter-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa.md?type=file&root=%252F). The final retained run took 3.442 s. Completion documentation and evidence/probe packaging are separately identified in the closeout manifest. No live model or key has been used.
