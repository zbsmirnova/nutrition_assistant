# W001 independent QA — attempt 1

Date: 2026-09-22.
Reviewer: separate QA agent, independent_m1_qa.
Review type: independent requirement/source review and test design; database execution assisted by the lead assistant.
Verdict: **pass for the stated local W001/M1 scope**, with two nonblocking documentation observations to correct during closeout. No production-release verdict is implied.

## Identity and scope

Work brief: [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F), W001-A01 through W001-A12.

Base commit: 0500e9918dad269d5e74ff11f13c05fedb55af83. The reviewed source contains uncommitted work; the base commit alone is not the reviewed revision.

Frozen source ID: 7eb70aa8e2166b5a64bf218b5674adab55eefe02d10c32af8ff2aff4230e5c57.

Archive: [w001-7eb70aa8e216.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w001-7eb70aa8e216.tar.gz?type=file&root=%252F).
Archive SHA-256: 9ee20613c0ebbb2d3ba0091f736cdabb146682b319ba48bceb7180366345fe5c.
Manifest: [001-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-source-manifest.json?type=file&root=%252F).

The QA reviewer verified the archive hash, all 72 manifest file hashes before and after the review, and independently recomputed the source ID from compact, sorted-key JSON containing base_commit and files. All matched. The isolated extracted source and all production-source hashes remained unchanged. Only QA probes/evidence and a virtual-environment symlink were added to the isolated copy; QA did not edit the main workspace, stage, commit, or deploy.

Scope: already resolved product-food additions, deterministic food/day values, ownership, immutable prepared operations, atomic results/outbox, safe retries and process recovery, pinned catalog versions, and fake delivery. Requirements and accepted decisions were read before inspecting developer test coverage. Relevant source, migrations, contracts, numeric policy, and outbox behavior were reviewed directly.

## Environment and execution attribution

QA measured macOS 26.5.2 arm64 and Python 3.14.0. The isolated copy reused the main project's installed virtual environment. Measured packages: SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg 3.3.6, psycopg-binary 3.3.6, Pydantic 2.13.5, jsonschema 4.26.0.

The lead supplied the existing local PostgreSQL 17.11 container on localhost port 55432. Database suite execution confirmed migration head 0002 in fresh random schemas. PostgreSQL version was supplied in the environment handoff rather than queried directly by this QA agent. No shared public demo records were modified by the QA suites; tests created and removed their own ntest_ or nqa_ schemas.

Two attempts to launch the database suite from the QA agent's escalation context were interrupted without execution results. Database commands were therefore executed by the lead through its approved root tool in the same isolated copy. The QA agent authored the independent probes and assessed the resulting raw outputs itself. This is independent review/test design with root-assisted execution, not a claim that every command was personally executed by QA.

| Check | Executor and observed result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | QA agent: 41 passed in 0.374 s; 32 contract and 9 arithmetic tests. |
| `.venv/bin/python -m unittest discover -s tests/integration -v` | Lead at QA request: 26 passed in 9.545 s, exit 0. QA read and assessed the saved output. |
| `.venv/bin/python -m unittest qa_independent -v` | Lead at QA request: 10 independently authored probes passed in 2.384 s, exit 0. QA read and assessed the saved output. |
| Snapshot integrity | QA: archive hash, recomputed source ID, and all 72 file hashes matched; unchanged after execution. |
| Source and document review | QA: service, schema, both migrations, arithmetic, outbox, relevant contracts/specifications/ADRs, setup, brief, and developer report inspected. No substantive implementation defect confirmed. |

Raw database logs: [001-integration-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-integration-output.txt?type=file&root=%252F) and [001-independent-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-independent-output.txt?type=file&root=%252F).
Their respective SHA-256 values are 31c2bc9a585bb1b7624b1bcb9cb4a2acfe0cdffae353c7a62ca6d58a03704286 and 5f2c7109bd88934bbd851e02806bd131dc9ba0afa70f1ce71568d6db1df018e4.

Independent probe source: [test_w001_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w001_independent.py?type=file&root=%252F).
Probe SHA-256: 72dcd7343d2a374eeb1e9b4018a6ce6edf9bd17a6ec54d7d22ad94ca2ecc5808.

To reproduce, extract the identified archive into a separate writable directory, install its pinned runtime dependencies, start its documented local PostgreSQL service, place the byte-identical retained probe beside the extracted source with the module name qa_independent.py, and run the three commands above. Each database test creates its own schema; no existing rows are required. Retaining the probe under a separate QA test directory is appropriate, provided its hash and separate discovery command are recorded.

## Independent checks and reasoning

The probes supplement developer-authored tests with failure boundaries and cases derived from the requirements. Shared synthetic seed helpers were inspected and reused only for setup; expectations were independently specified.

| Probe | Independent expectation and observed result |
| --- | --- |
| QA01: fractional volume, bounds, zero, unknown | 37.5 ml at 83.2 kcal/100 ml gives 31.2 kcal, bounds 30–33; 7.2 g protein/100 ml gives 2.7 g. Explicit zero fat is complete zero; missing carbohydrate is unknown. Persisted volume and day query match. Passed. |
| QA02: catalog change after prepare; historical replay | Prepare 125 g against version 1, make version 2 current before execution, then execute. The frozen command still returns 125 kcal from version 1. After a separate 25 kcal addition, replay returns the original 125 kcal day snapshot while a fresh day query returns 150 kcal. Passed. |
| QA03: real outbox INSERT failure | A database trigger fails the outbox insert after food/result writes. Food/day/revision/component/applied/outbox rows and user revision all roll back; prepared input survives. Removing the test trigger and retrying produces one result. Passed. |
| QA04: deferred failure at COMMIT | A deferred constraint trigger fails only at commit, after the before_commit callback. No result is returned and no mutation/outbox survives; no after_commit callback occurs. Retry succeeds once after removing the trigger. Passed. |
| QA05: owned plus foreign component | A command mixing an owned product and another user's product rejects the entire addition; no partial food or success response is stored. Passed. |
| QA06: populated upgrade | Downgrade a populated disposable schema to 0001, then upgrade to 0002. Source identity, bot mapping, frozen outcome, and outbox payload survive; inbox immutability is restored. Passed. |
| QA07: failed upgrade rollback | Construct legacy 0001 inbox rows that conflict under bot-wide uniqueness. Upgrade fails explicitly, leaving version 0001, both rows, the original columns, and the immutable-update trigger intact. No silent data deletion or partially applied migration. Passed. |
| QA08: concurrent inbox delivery | Six simultaneous identical deliveries produce one source ID and one inbox row. Passed. |
| QA09: incompatible concurrent payloads | Two different quantities compete for the same operation identity. Exactly one succeeds, the other raises Conflict, and one entry/outbox matches the winner. Passed. |
| QA10: frozen timezone/date | After preparing an explicitly backdated command from a DST-transition source instant, change the user's configured timezone. Execution preserves the original date, source instant, source timezone, day timezone, and entry timezone. Passed. |

The migration collision check intentionally expects a failure. Automatic reconciliation of already conflicting legacy data is outside this synthetic slice; preserving all original state is the required safe result.

## Acceptance coverage

All rows refer to the frozen source revision and the executions recorded above. Existing integration tests were inspected as executable evidence; independent probes and source review provide additional coverage.

| Criterion | Evidence and result |
| --- | --- |
| W001-A01 | Fresh/repeated migrations, metadata comparison, current-pointer constraints, and downgrade/upgrade pass in isolated schemas. QA06/QA07 additionally verify populated preservation and transactional failure. Passed. |
| W001-A02 | Existing 250 g case verifies one entry/revision, 250 kcal, 10 g protein, 10 g fat, 30 g carbohydrate, day/entry reads, and outbox correspondence. QA01 independently checks fractional scaling and bounds. Passed. |
| W001-A03 | Sequential and concurrent operation replay, new identical-text consumption, and bot-scoped identity pass. QA08 verifies concurrent source acceptance; QA09 verifies incompatible simultaneous reuse. Passed. |
| W001-A04 | Existing child-process crash before commit leaves no mutation/outbox and retry applies once. QA03/QA04 add actual SQL insertion and commit-time failures, checking all mutation tables and user revision. Passed. |
| W001-A05 | Existing real child process exits after commit; a new processing process recovers the same stored result and a separate fake sender delivers it without another entry. Passed. |
| W001-A06 | Application actor/source/product/operation/entry guards and owned database source/current-parent constraints pass. Another user's day is empty. QA05 adds mixed-component rollback. Passed within the trusted local actor boundary. |
| W001-A07 | Existing unknown/partial/empty and mixed-component tests pass. QA01 persists explicit known zero alongside unknown carbohydrate and confirms their distinct result variants. Passed. |
| W001-A08 | Existing catalog-update/history and snapshot-update constraints pass. QA02 also changes the catalog between prepare and execute; pinned version/source/policy and historical outcome survive. Passed. |
| W001-A09 | Committed row/result/outbox agreement, changed request rejection, overflow rollback, and crashes pass. QA03/QA04 confirm that even a commit-time failure cannot return success; QA09 adds competing incompatible requests. Passed. |
| W001-A10 | Four concurrent distinct additions yield day result entry counts 1–4 and final 1000 kcal, with no lost update. Source review confirms mutation and summary reads are under the same user lock. Passed. |
| W001-A11 | Existing delayed child-process execution preserves original source instant and explicitly targeted date. QA10 adds profile timezone changes and a source near the DST transition. No wall-clock date is substituted. Passed. |
| W001-A12 | All 41 contract/arithmetic checks remain green; generated-schema drift test passes. Setup, dependencies, accepted technical decisions, specifications, and handoff exist and describe the local scope. Two stale wording observations remain for documentation-only closeout below. Passed with nonblocking documentation observations. |

## Defects and disposition

No blocking or substantive implementation defect was confirmed.

**W001-QA-D01 — low, stale stack status.** The lead identified and QA confirmed that [architecture-plan.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/architecture-plan.md?type=file&root=%252F) still says Python/PostgreSQL is a candidate. D003 and the implemented runtime establish the accepted M1 choice. Reproduce by reading the paragraph after module responsibilities. Expected: distinguish accepted M1 dependencies from future transport choices. Actual: the older candidate wording remains. Disposition: lead agreed to correct during documentation closeout; no runtime retest required for that wording change.

**W001-QA-D02 — low, stale numeric status.** The lead identified and QA confirmed that [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F) refers to proposed database precision. D006 accepts the implemented numeric policy. Expected: describe that accepted policy accurately. Actual: the obsolete proposed label remains. Disposition: lead agreed to correct during documentation closeout; no runtime retest required for that wording change.

These are present in the reviewed snapshot. This report does not claim that later documentation edits have already occurred or were included in that source hash.

## Coverage limits and verdict

This review does not exercise live LLM interpretation, actual Telegram ingress/delivery/authentication, recipes, pending conversation/corrections, observations, scheduling, RLS, production deployment, deletion/retention, server restart, backup restore, or load/performance limits. The timezone probe preserves already resolved evidence; it does not validate a future natural-language date resolver or scheduler. The fake outbox does not establish exactly-once externally visible messages. Trusted local application actors and synthetic catalog data are the intended boundary.

The QA agent did not recreate the host's Python environment or Docker image from scratch; dependencies were measured and migrations were run repeatedly in fresh isolated schemas. Database execution was root-assisted as disclosed. QA did not independently rerun git diff --check on the unrelated main working tree; the source archive is a frozen export without Git metadata. Parent closeout owns final document links, formatting, retained evidence, and status updates.

**Verdict: pass for W001/M1 at the frozen source ID above.** All 12 applicable acceptance criteria have evidence, with no blocking findings. Correct the two low-severity documentation labels, preserve/link this report and probe/output evidence, and update the work brief and roadmap according to their completion rules. Any such post-review documentation/test packaging must remain explicitly distinguished from the reviewed source snapshot. No production-source fix or behavioral recheck is required by this review.

## Lead closeout addendum — 2026-09-22

The review and verdict above were authored by independent_m1_qa. The lead retained the report and corrected its evidence links to durable repository locations; the reproduction sentence names the scratch probe module explicitly. The original reviewer artifact is preserved as [w001-independent-report-original.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w001-independent-report-original.md?type=file&root=%252F), SHA-256 fab689921ea74edfe85970d93a4a494e02826d8736f6400cdb4508adf41de6a8. This addendum records lead actions and is not additional independently executed QA.

W001-QA-D01 and W001-QA-D02 are resolved: the architecture now identifies the accepted M1 stack, and the contract guide identifies the accepted D006 database precision. The brief and roadmap now record W001/M1 complete. Setup and contributor/QA instructions include the retained independent suite.

The probe was copied byte-for-byte to [test_w001_independent.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/qa/test_w001_independent.py?type=file&root=%252F); its SHA-256 remains the value recorded above. The lead verified the retained command from the main repository:

~~~sh
.venv/bin/python -m unittest discover -s tests/qa -p 'test_w001_independent.py' -v
~~~

Observed: 10 tests passed in 2.390 seconds, exit 0. The existing 41 and 26 suites were not rerun for documentation-only edits. A direct lead execution of the application's db-info command returned PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2), schema public; this read changed no records.

After closeout, all original application, contract, dependency, migration, configuration, fixture, and test hashes still match the 72-file reviewed manifest. The archive hash also matches. Seven originally captured Markdown files changed: contributor instructions, root README, architecture overview, QA strategy, roadmap, typed-contract guide, and work brief. Reports/logs and the byte-identical independent probe were added outside the frozen source snapshot. These additions and document changes do not alter the reviewed production implementation. Final local-link and formatting checks are recorded in [001-closeout-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-closeout-manifest.json?type=file&root=%252F).
