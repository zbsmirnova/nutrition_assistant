# W002 independent QA — attempts 1 and 2

Date: 2026-09-22. Reviewer: separate QA agent, independent_m1_qa.
Review type: independent requirement/source review and probe design; database execution assisted by the lead assistant.
Final verdict: **pass for W002 private Telegram transport on attempt 2**, with one identified receipt-validation defect fixed and independently rechecked. This does not complete M2 or establish live Telegram or production readiness.

## Exact revisions and integrity

Base commit for both snapshots: 0500e9918dad269d5e74ff11f13c05fedb55af83. Both include uncommitted work; the base commit alone is insufficient to reproduce the review.

| Revision | Source ID | Archive SHA-256 |
| --- | --- | --- |
| Attempt 1 | 8cae828c2e8fe22c956dbb35a34236e530cf8591545d3233d63c67543cce4a0f | 1b943f03f29c46daf6079c2fe2cc98f63c5d4632020e67132311f68c9e0c437f |
| Attempt 2, fixed | 4ba4769b0cddba32ece9d2b001011ce51ef7614c694d5964c19c22b1c30f2ba2 | dfdca2d2eade182f1c7b3c0d82d475f847d301ef7781f1f46e0ae8c0ab626963 |

Archives: [w002-8cae828c2e8f.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-8cae828c2e8f.tar.gz?type=file&root=%252F), [w002-4ba4769b0cdd.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-4ba4769b0cdd.tar.gz?type=file&root=%252F).

Each archive contains 82 manifest-listed files. QA extracted each into its own temporary directory, verified the archive digest and all file hashes, and independently recomputed the source ID from compact sorted-key JSON containing base_commit and files. All matched before testing and after the final rechecks. Neither extracted snapshot's production source was edited. QA added only standalone probes/evidence and a symlink to the existing virtual environment; the main workspace was not edited by QA.

QA reviewed the complete five-file delta. The sole production-code change is strict positive-integer validation of the returned receipt chat ID in the Telegram adapter. The protocol test adds malformed chat-ID regressions; three documents refresh transport status and the handoff. Database, migration, polling, rendering, and outbox code are unchanged. Accordingly, attempt 1 database evidence is explicitly inherited for attempt 2, with targeted receipt/protocol rechecks instead of claiming a full database rerun on the fixed snapshot.

## Requirements, environment, and attribution

Inputs: constitution, W002 brief and criteria A01–A08, D007, relevant M1 persistence/execution decisions, QA strategy, setup and architecture/data-model documents. Source review covered transport normalization, owner linking, polling locks/cursors, rendering, receipt/error classification, migration 0003, service hash compatibility, outbox changes, CLI verification, and existing tests. The developer report was read separately from the independent expectations.

Measured QA runtime: macOS 26.5.2 arm64; Python 3.14.0; SQLAlchemy 2.0.54; Alembic 1.20.0; psycopg/psycopg-binary 3.3.6; Pydantic 2.13.5; jsonschema 4.26.0. The installed environment was reused, not recreated from scratch. Local PostgreSQL 17.11 was supplied by the lead's environment handoff; QA did not directly query its server version. Migration head 0003 and model equivalence are exercised by the integration suite.

QA personally ran offline checks and authored the six W002 probes. The lead inspected and executed database commands at QA's request through the approved root tool, inside the isolated attempt 1 snapshot. QA read and assessed the actual executor-attributed raw logs. All API responses and records were synthetic; no test invoked real Telegram or a model. Each database test created and removed only its own random schema.

| Execution | Executor, exact revision, result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | QA, attempt 1: 52 passed in 0.391 s. |
| `.venv/bin/python -m unittest discover -s tests/integration -v` | Lead at QA request, attempt 1: 38 passed in 13.288 s; exit 0. |
| `.venv/bin/python -m unittest discover -s tests/qa -v` | Lead at QA request, attempt 1: 10 retained M1 checks passed in 2.493 s; exit 0. |
| `.venv/bin/python -m unittest qa_w002_independent.ReceiptProtocolQA -v` | QA, attempt 1: one test failed in the boolean and float subcases; the string subcase passed. Reproduced in 0.002 s for preserved failure output. |
| `.venv/bin/python -m unittest qa_w002_independent.TransportDatabaseQA -v` | Lead at QA request, attempt 1: five independent database probes passed in 1.272 s; exit 0. |
| `.venv/bin/python -m unittest qa_w002_independent.ReceiptProtocolQA -v` | QA, attempt 2: the byte-identical independent test passed all three subcases in 0.001 s. |
| `.venv/bin/python -m unittest discover -s tests -p test_telegram.py -v` | QA, attempt 2: all 11 protocol/rendering checks passed in 0.006 s. |
| `.venv/bin/python -m unittest qa_w002_retained.ReceiptProtocolQA -v` | QA, attempt 2: the separately identified retention copy passed in 0.001 s. |

Attempt 1 raw logs: [002-qa-integration-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-integration-output.txt?type=file&root=%252F), [002-qa-retained-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-retained-output.txt?type=file&root=%252F), [002-qa-independent-db-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-independent-db-output.txt?type=file&root=%252F), and [002-qa-receipt-original-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-receipt-original-output.txt?type=file&root=%252F).

Attempt 2 raw logs: [002-qa-receipt-recheck-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-receipt-recheck-output.txt?type=file&root=%252F), [002-qa-protocol-recheck-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-protocol-recheck-output.txt?type=file&root=%252F), and [002-qa-retained-receipt-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-qa-retained-receipt-output.txt?type=file&root=%252F).

## Independent probes

| Probe | Requirement-derived expected result and observation |
| --- | --- |
| QA01: receipt identity types | A receipt for chat 1 with chat.id true, 1.0, or "1" is malformed and must remain uncertain. Boolean/float cases failed on attempt 1; all pass on attempt 2. |
| QA02: SQL checkpoint failure | Fail the cursor UPDATE through a test-only database trigger. Accepted source remains committed, cursor stays at 0, and the session lock is released. After removing the trigger, a new poller reuses the same source and advances to 78. No food/result/outbox is created. Passed. |
| QA03: committed batch prefix | In an out-of-order batch, a valid update commits before a later malformed supported update fails. Cursor stays at 0. Correcting the malformed fixture and replaying produces exactly two sources, retaining the original source identity; no food is created. Passed. |
| QA04: source metadata replay | Reuse an accepted update with a different reply ID or removed forwarding evidence. Both attempts raise Conflict; the original source ID, reply 55, and forwarding flag remain unchanged. Passed. |
| QA05: send outside transactions | During the injected API call, a separate connection reads the committed domain outcome and acquires user/outbox row locks with NOWAIT. The claim is committed as sending with one attempt. A valid receipt 707 is then stored as sent. Passed. |
| QA06: competing account provisioning | Two owners concurrently link the same bot/user/chat identity. Exactly one succeeds; only one mapping exists. Subsequent input resolves to that mapped owner despite another owner's ID in the text. No food is created. Passed. |

The five database probes passed on attempt 1. Their covered code is unchanged in attempt 2; the valid integer receipt in QA05 also satisfies the new guard. This inheritance is based on the reviewed source delta, not a claim that the same database command ran on both revisions.

Original probe [w002-independent-probes-original.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-independent-probes-original.py?type=file&root=%252F) SHA-256: 01436b8757c82321726a60aa3cc5b5154ae4f8b81307a0d41ea407ff00bb776e. Reproduction copies this file as qa_w002_independent.py at the extracted snapshot root and uses the commands above.

Approved retention copy [test_w002_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w002_independent.py?type=file&root=%252F) SHA-256: fda84a3283837fce4f7e823c1130812b79ea5e1770caba6a9f045f4ec0d9bc80. QA verified its only difference: import the application ROOT and use ROOT for fixture lookup, allowing placement in the repository's QA test directory. Assertions and database probes are unchanged. Preserve the original artifact and both identities; do not silently replace the original probe hash.

## Defect and recheck

**W002-QA-D01 — low severity, malformed receipt accepted; resolved.** Affects D007 and W002-A07. The first snapshot compared the returned chat ID using Python equality, which treats true and 1.0 as equal to integer 1. A synthetic successful API response with message_id 7 and either malformed chat value therefore made TelegramSender return 7 rather than raise TelegramUnavailable. The worker would treat that return as sent. This did not change the requested destination or cause an unauthorized send, but incorrectly classified an invalid success response.

Reproduce with QA01 against attempt 1. Expected: malformed receipt stays uncertain. Actual: boolean and float receipts accepted; string already rejected. The preserved failure output records both failing subcases.

Fix: require positive_id on the returned chat ID before comparing it with the requested private chat. The lead supplied attempt 2, which QA independently verified. The unchanged independent probe now passes all cases, and all 11 protocol/rendering checks pass. No unresolved substantive defect remains. Earlier failure evidence and source identity are retained rather than relabeled as passing.

## Acceptance coverage

| Criterion | Evidence and final assessment |
| --- | --- |
| W002-A01 | Existing private sender/chat/bot mapping and unsupported/group/bot/media/edit rejection checks pass. QA06 independently exercises competing provisioning and claimed owner text. CLI verifies configured bot identity before transport execution. Passed within the explicitly provisioned private boundary. |
| W002-A02 | Existing source instant/timezone/reply/forwarding tests pass. QA04 checks immutable replay of changed metadata; QA06 confirms text cannot choose the owner. Passed. |
| W002-A03 | Existing real process exit before checkpoint and competing-poller tests pass. QA02 adds actual checkpoint SQL failure and released-lock recovery; QA03 adds a committed batch prefix followed by failure. Cursor advances only after accepted sources commit. Passed. |
| W002-A04 | Existing populated 0002→0003 upgrade, old hash/result replay, metadata comparison, and retained M1 migration probes pass. No migration change occurred in attempt 2. Passed. |
| W002-A05 | Existing bot-scoped claim/expiry and successful-receipt checks pass. QA05 independently verifies committed outcome visibility, absence of domain/claim row locks during send, and stored message ID. Passed. |
| W002-A06 | Offline rendering checks verify Russian entry values and dated historical day totals, unknown/partial/zero distinctions, bounded Unicode descriptions, no parse mode, and disabled previews. These checks passed on both original and fixed transport code. Passed. |
| W002-A07 | Existing explicit-rejection, bounded delayed retry, server/network ambiguity, and error-redaction checks pass. QA01 found a malformed receipt gap; strict-type fix and independent recheck resolve it. Passed after attempt 2. |
| W002-A08 | Offline bot identity/webhook checks verify refusal without deletion; CLI source and setup document explicit configuration and one-batch/one-send behavior. No test makes live calls. Passed for synthetic verification. |

## Limits and completion

This review verifies the private transport slice using injected API responses and local PostgreSQL. It does not measure a live bot, HTTPS behavior against Telegram, natural-language interpretation, provider/data-sharing choices, pending actions, corrections, recipes, observations, scheduling, public onboarding, media/edit workflows, operational supervision, retention/deletion, hosting, or production deployment. Received text remains inbox evidence and never automatically becomes food. Synthetic end-to-end checks supply an explicit resolved fixture command.

Real external visible delivery is not exactly once. Malformed supported input intentionally prevents cursor advancement for investigation; unattended recovery/operator tooling is outside this slice. Database execution was root-assisted, as recorded. No new dependency installation or clean-container build was independently repeated.

**Final verdict: pass for W002 at source 4ba4769b0cddba32ece9d2b001011ce51ef7614c694d5964c19c22b1c30f2ba2**, supported by inherited unchanged-code evidence and the explicitly listed targeted rechecks. Close W002 after preserving/linking this report, probe artifacts and logs, and updating its brief/status documentation. Keep M2 in progress. Later report packaging, retained-test additions, and status edits are post-review changes and must remain distinguished from the frozen snapshot.

## Lead closeout addendum

The lead preserved the original independent report as [w002-independent-report-original.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-independent-report-original.md?type=file&root=%252F), SHA-256 28d7352c7d50c41f332de5e4d8bd23be6a4c9a0dadd2effd5ac5a0954f0f794b. This retained report changes only evidence links/reproduction filename and adds this explicitly attributed closeout; its independent findings and verdict are preserved.

The QA-approved retention copy was saved byte-for-byte as [test_w002_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w002_independent.py?type=file&root=%252F). The lead executed the repository command below after packaging: six tests passed in 1.218 s, exit 0. This execution used attempt-2 production code and is lead verification, distinct from the independent executions above.

~~~sh
.venv/bin/python -m unittest discover -s tests/qa -p test_w002_independent.py -v
~~~

W002 is done, with W002-QA-D01 resolved. M2 remains in progress. Post-review changes update the root README, roadmap, QA strategy, and W002 brief; add the approved regression copy and evidence files; and retain the original source/probe/report artifacts. Production, migrations, dependencies, and existing test files remain identical to the reviewed attempt-2 snapshot. [002-closeout-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-closeout-manifest.json?type=file&root=%252F) records final hashes and documentation checks.
