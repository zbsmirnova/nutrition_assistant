# QA report — W004 / attempt 2

## Identity and scope

Date: 2026-09-22. Reviewer: independent_m1_qa, separate independent QA agent.
Verdict: **pass for all eight W004 criteria within the simulated Nebius transport scope**. The original Retry-After defect is resolved. No live-model compatibility, language quality, M2 completion or production-release claim is made.

Source ID: d31d4079dfe8ecf0cae2309ad734f1bcf5d347cc31b37294811d7fd1d1492087.
Base commit: 7bea583d1f567e0971d48993bccfc59b35d8a5ae.
Archive SHA-256: e2a4c3047e88267d1322b1693226de1c1e02dd35c4de2f5c8264a4d97841f124.
Manifest: [004-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-source-manifest.json?type=file&root=%252F).

QA verified all 105 file hashes, the archive digest, and source ID computed as SHA-256 of compact sorted-key JSON for the ordered files list, excluding base_commit. Final recheck found no reviewed-source changes. The lead separately reported all 68 runtime/prompt/test/contract/dependency/migration files in its workspace still matched. QA wrote only its own scratch artifacts. Later documentation, report relocation and retained-probe packaging are outside the frozen source identity.

Review inputs: constitution, W004 brief A01–A08, D009/D012, W003 worker/recovery requirements and QA strategy. Source review covered configuration, fixed HTTPS request path, prompt/context projection, generated schema use, completion validation, error/retry classification, worker claims and command recovery, explicit CLI and smoke behavior. The supplied official structured-output documentation example supports the direct json_schema request form and model-dependent support; reading that example is not a successful API/schema compatibility test.

Measured environment: macOS 26.5.2 arm64; Python 3.14.0; SQLAlchemy 2.0.54; Alembic 1.20.0; psycopg and psycopg-binary 3.3.6; Pydantic 2.13.5; jsonschema 4.26.0. Existing virtual environment reused. PostgreSQL 17.11 is the supplied local environment, not independently queried by QA. Migration head remains 0004; no migration or dependency change. Every DB check uses synthetic data in its own random schema.

## Checks and evidence

Expected independent outcomes were derived from privacy projection, valid HTTP delay handling, resource cleanup, smoke semantics and durable retry requirements. Existing developer tests supplement this review; they are not its sole evidence. QA personally executed offline checks. The lead executed database commands through its approved root tool, and QA assessed the source and actual output independently.

| Check | Actual result | Executor and revision |
| --- | --- | --- |
| Default offline discovery | 79 passed in 0.738 s | QA personally, frozen attempt 2. |
| Unchanged independent protocol probes | Four passed in 0.066 s | QA personally, frozen attempt 2. |
| Explicit PostgreSQL integration discovery | 59 passed in 15.480 s | Lead/root, frozen attempt 2; QA assessed output. |
| Independent HTTP-date durable retry probe | One passed in 0.337 s | Lead/root at QA request, attempt 2; QA assessed output. |
| Retained QA discovery | 32 passed in 3.442 s | Lead/root workspace with matching runtime and approved retention-only diff. Includes the previous 27 plus these five probes; this is a rerun, not 32 new independently designed checks. |

Raw evidence: [004-qa-unit-attempt2-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-qa-unit-attempt2-output.txt?type=file&root=%252F), [004-qa-protocol-attempt2-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-qa-protocol-attempt2-output.txt?type=file&root=%252F), [004-developer-integration-attempt2-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-integration-attempt2-output.txt?type=file&root=%252F), [004-qa-db-final-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-qa-db-final-output.txt?type=file&root=%252F), [004-developer-retained-final-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-developer-retained-final-output.txt?type=file&root=%252F).

Reproduce with PYTHONDONTWRITEBYTECODE=1 and the reviewed snapshot's interpreter: from its root, `-m unittest discover -s tests -v` and `-m unittest discover -s tests/integration -v`; from the QA probe directory, set W004_SOURCE_ROOT to the reviewed source directory and run `-m unittest qa_w004_independent.ProtocolQA -v` and `-m unittest qa_w004_independent.RetryDatabaseQA -v`. Database commands need the documented local PostgreSQL environment; the independent probe asserts a localhost address and owns only a random nqa4 schema. Retained packaging is checked with `-m unittest discover -s tests/qa -v` from the project root.

| Criterion | Assessed evidence and expected behavior | Status |
| --- | --- | --- |
| W004-A01 | Configuration validates secret/model presence and bounded character shapes without echoing values; invalid configuration exits before network/database use. Import/configuration does not start requests. No dependency or migration changes. | Passed |
| W004-A02 | Standard HTTPSConnection uses certificate-verifying defaults, fixed origin/path and bearer header; one request, non-streaming single completion, 30-second socket timeout and 256-KiB limits. Simulated checks prove redirects are not followed, error bodies are not read, oversized inputs/outputs reject, and local schema constraints match the generated ParserOutput export apart from document-identification metadata. No provider/schema fallback. | Passed for construction and simulated protocol |
| W004-A03 | Independent QA02 supplies malicious catalog text and additional owner/version/Telegram/observation keys. Only the six allowed candidate fields appear; source/catalog text remains in the user data message and never becomes system instructions. Catalog overflow makes no request. Source date/time zone remain explicit, with no history or unrelated observations projected. | Passed for context projection |
| W004-A04 | Existing envelope/schema/reference cases reject refusal, truncation, tool/function calls, malformed content, multiple choices and foreign references. Independent QA03 makes response reading fail with sensitive-shaped diagnostic text: connection closes once, no retry loop, smoke exits with a generic sanitized error and no database engine. Worker rejection tests show no prepared food or outbox and no provider payload in diagnostics. | Passed |
| W004-A05 | Permanent HTTP/invalid completion failures terminate visibly; transient network/408/429/5xx failures enter the durable three-attempt budget. Independent QA01 now preserves 120-second hints with trailing SP/HTAB and rejects over-one-day hints. QA05 proves an HTTP-date hint persists at least until its requested instant, a recreated worker waits without calling the provider, and a later due retry succeeds once. Existing tests verify bounded exhaustion and fallback delay. | Passed after D01 fix |
| W004-A06 | Fingerprint covers model, prompt, schema, generation policy, endpoint and transport limits; key rotation leaves it unchanged. Changed model/interpretation identity fences unfinished work. Independent QA05 rotates the key between delayed attempts and checks replay makes no additional provider request or food/outbox. Existing provider-specific and W003 recovery tests preserve prepared/applied commands without parsing again. | Passed |
| W004-A07 | CLI requires explicit owner/source for live worker operation, prints sanitized status, and does not process other inputs. Fixed smoke runs resolver validation without a database and prints validation flags/fingerprint only. Independent QA04 rejects an incorrect 99-g proposal; valid fixture passes existing tests. Provider-worker integration retains backend arithmetic, authorization and missing-dairy-fat deferral. | Passed with injected responses |
| W004-A08 | Exact source and archived failure/recheck identities, runtime versions, raw outputs, original probe hash and root execution attribution are recorded. No live provider/model, language accuracy, latency/cost or real Telegram evidence is claimed. | Passed |

## Defect and revision-specific recheck

**W004-QA-D01, medium, A05 — resolved in attempt 2.** In the original snapshot, HTTP 429 with `Retry-After: 120 ` or a trailing tab yielded a 60-second fallback rather than the valid requested 120 seconds; `86401 ` incorrectly became retryable instead of hitting the terminal one-day policy. QA reproduced this through the real standard-library header parser and a mocked HTTPS connection. Expected values and failure output remain preserved.

The final four-file delta adds SP/HTAB normalization after the existing raw type/length bound, replaces date rounding with math.ceil so an exact one-day date remains permitted, and bumps the adapter fingerprint to nebius-chat-v2. Developer regressions include whitespace and exact-day boundaries; D012 records normalization and D009 clarifies historical wording. QA reviewed the entire delta and reran the unchanged original probe: all three failed subcases now pass. No changes to worker transactions, migration, service or transport followed.

Original source: 3b4ee706e7d0fab4b917d9711c2355da08cba8a3d6f2eb89c56ec64f15fdb205. Original report [004-nebius-adapter-qa-attempt1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa-attempt1.md?type=file&root=%252F), SHA-256 e880ea9100fb1abd8e3cb0fabac2698fad2e37ea13f007177afdf4f11b26c838, remains unchanged. It records 79 passing original offline checks, 59 original root-assisted integration checks and 27 earlier retained checks, alongside the failing independent whitespace case. Those earlier runs are not relabeled as final evidence. The original report also documents a corrected probe-authoring schema-metadata assertion and separately retained preliminary artifacts; that was a test-harness issue, not an additional product defect.

## Probe identity and retention

Original [004-original-qa_w004_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-original-qa_w004_independent.py?type=file&root=%252F): SHA-256 594ce71f502d42211f98e87e069395582d1c48569c8caffc6434a5da468d31a1. It remains byte-identical between original failure and passing recheck.

Retained [test_w004_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w004_independent.py?type=file&root=%252F): SHA-256 d5cc683d759e6a432ef34070e75c9930934cca7d09df7f8f891db4eee022bca2. QA independently compared the diff and approved removal only of scratch Path/sys/SOURCE import injection. Imports needed for environment tests remain; no assertion, fixture, query or expected outcome changes. This packaging copy is outside the 105-file source snapshot and has its own execution evidence.

## Coverage limits and verdict

No real provider request or real key was used; no model was selected. TLS server behavior and actual model/schema compatibility remain live checks, despite verified use of standard HTTPS defaults. The prompt/context tests do not establish universal prompt-injection resistance. The socket timeout bounds inactivity, not total request duration; worker leases fence late results, and uncommitted inference may incur repeated billing. The independent retry probe recreates worker objects, while actual process-crash evidence comes from the retained worker/integration tests.

No general Russian-language evaluation, clarification/correction expansion, real Telegram send, personal-data processing, hosting, retention/export/deletion behavior or production operation was exercised. No removed evaluation corpus was recreated. No live latency/cost result is claimed.

**Pass for the exact attempt-2 W004 snapshot and its eight scoped criteria.** No unresolved blocking or additional nonblocking finding remains. The lead may complete documentation/evidence closeout and its authorized commit workflow, preserving this reviewed source identity and distinguishing later packaging changes. Further live verification requires the separately configured secret/model and an explicit request; this review does not initiate it.

## Lead closeout addendum

The original independent report is retained byte-for-byte as [004-nebius-adapter-qa-original.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-nebius-adapter-qa-original.md?type=file&root=%252F) (SHA-256 cca21ccd992fdb9ffa339aa17ede7ec5098dd64320175d0a3f6d1e6061d6c6cc). This maintained copy changes evidence links and adds this explicitly attributed closeout. The original failed report, independent probe, preliminary probe-authoring artifact and execution logs are retained separately and unchanged. Repository QA discovery uses the approved retained probe copy.

W004 is done; M2 remains in progress. Final project checks total 170 (79 offline + 59 integration + 32 retained QA). After review, only completion/setup/roadmap/QA documentation and retained evidence/probe packaging changed. All 68 reviewed runtime, prompt, existing test, contract, dependency and migration files still match attempt 2. [004-closeout-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/004-closeout-manifest.json?type=file&root=%252F) records the comparison and final artifact hashes. No live inference or Telegram activity was initiated during closeout.
