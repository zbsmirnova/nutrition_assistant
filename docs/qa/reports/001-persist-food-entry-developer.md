# W001 developer verification — attempt 1

Date: 2026-09-22.
Reviewer: lead assistant acting as developer.
Review type: developer verification, not independent QA.
Verdict: pass for the implemented M1 acceptance checks; independent QA remains pending.

## Revision and reproducibility

Base Git commit: 0500e9918dad269d5e74ff11f13c05fedb55af83.
The tested code includes uncommitted files; the base commit alone does not identify it. No commit or staging change was created for this review.

Source snapshot ID (SHA-256 of base commit plus sorted file/content hashes):

~~~text
7eb70aa8e2166b5a64bf218b5674adab55eefe02d10c32af8ff2aff4230e5c57
~~~

The 72-file manifest is [001-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-source-manifest.json?type=file&root=%252F). The local archive is [w001-7eb70aa8e216.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w001-7eb70aa8e216.tar.gz?type=file&root=%252F); archive SHA-256:

~~~text
9ee20613c0ebbb2d3ba0091f736cdabb146682b319ba48bceb7180366345fe5c
~~~

The archive contains source, contracts/fixtures, tests, migrations, dependencies, and the governing specifications/brief. It excludes the virtual environment, IDE files, secrets, legacy deployment configuration, and generated QA evidence. It is ignored by Git to avoid committing duplicate source. Preserve/share this local review artifact when handing off this working-tree revision; a clone of the base commit alone is insufficient.

Source hashes were captured before the final test runs and checked unchanged afterward. Verification report files are outside that source hash to avoid self-reference. The manifest and archive make previously untracked relevant files reproducible.

## Environment and commands

Host: Darwin arm64, Python 3.14.0.
Database: PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2), local Docker container, image digest pinned in [compose.dev.yml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/compose.dev.yml?type=file&root=%252F).
Dependencies: SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg/psycopg-binary 3.3.6, Pydantic 2.13.5, jsonschema 4.26.0.
Migration head: 0002.
Data: synthetic catalog values and randomly isolated test schemas only.

| Command / check | Observed result |
| --- | --- |
| python -m unittest discover -s tests -v, using the project virtual environment | 41 tests passed in 0.406 seconds: 32 contracts plus 9 arithmetic tests. |
| python -m unittest discover -s tests/integration -v, using the project virtual environment | 26 tests passed in 9.708 seconds against real PostgreSQL. Child processes deliberately exited with code 77 at before/after-commit boundaries and recovered as expected. |
| Local migrate and demo commands | Migrations applied; 250 g synthetic product yielded 250 kcal / 10 g protein / 10 g fat / 30 g carbohydrate; replay returned the same result and left one entry. |
| pip check | No broken requirements. |
| Docker Compose config validation | Passed. |
| Python compilation and git diff --check | Passed. |
| Source/archive SHA verification after final tests | All 72 source hashes and archive hash matched. |

Exact setup and runnable commands are in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F). Integration tests create/drop their own random schemas and do not reset the development database. They do not silently skip when PostgreSQL is unavailable.

## Acceptance coverage

All executable cases below are in [test_food_service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/integration/test_food_service.py?type=file&root=%252F); arithmetic checks are in [test_nutrition.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_nutrition.py?type=file&root=%252F). Expectations include independently specified sample values, but these tests were authored/executed by the developer and remain subject to separate QA review.

| Criterion | Evidence | Developer result |
| --- | --- | --- |
| W001-A01 | Fresh/repeated migrations, current model comparison, current-pointer FK inspection, isolated downgrade/upgrade. | Passed. |
| W001-A02 | 250 g calculation, saved row counts, entry read, day query, and committed outbox payload agree. | Passed. |
| W001-A03 | Sequential and concurrent replay; bot-wide delivery identity; new identical-text messages produce a second portion. | Passed. |
| W001-A04 | A child process exits before commit; entry/result/outbox are absent while accepted source/prepared command remain; another process applies it once. | Passed. |
| W001-A05 | A child process exits after commit; a new process recovers the identical outcome and another fake sender delivers the retained response; no new portion. | Passed. |
| W001-A06 | Foreign actor/message/product/operation/entry rejection; foreign-source and wrong-parent database constraints; another user's day is empty. | Passed. |
| W001-A07 | Unknown versus partial nutrient totals, mixed-component entry coverage, empty day versus explicit zero; pure arithmetic also checks known zero. | Passed. |
| W001-A08 | Product version change preserves the prior meal, source identity, calculation policy, and values; ordinary snapshot updates fail. | Passed. |
| W001-A09 | Returned entry/day values match committed rows; changed operation input fails; day overflow rolls back the second mutation and response; crash cases cover transaction boundaries. | Passed. |
| W001-A10 | Four concurrent distinct explicit additions are retained and final totals include all four; same-operation concurrency produces one mutation. | Passed. |
| W001-A11 | A near-midnight source with an explicitly backdated command is executed in another process; source instant, intended date, and time-zone evidence remain unchanged. | Passed. |
| W001-A12 | Contract suite remains green; current setup, architecture, accepted decisions, numeric policy, roadmap, and handoff documents are updated. | Passed under developer checks; independent review outstanding. |

Additional delivery checks cover competing claims, expired-token acknowledgment rejection, visible uncertain sends without blind retry, and a limit of three proven-unsent attempts.

## Defects and limitations

No unresolved failing developer check was observed for this scope. The initial migration generation required explicit deferred current-pointer constraints, and bot-wide delivery uniqueness was tightened in migration 0002 before the final run. These are resolved implementation changes, not outstanding defects.

Not exercised/implemented: live model parsing, real Telegram authentication or delivery, a recipe engine, clarification/correction workflows, daily observation commands, scheduler/DST delivery, RLS, production deployment, retention/export/deletion, or a PostgreSQL-server restart/backup restore. The recovery checks restart application/sender processes against the persistent database; they do not claim server disaster recovery.

The CLI assumes a trusted development operator. M1 accepts one frozen resolved command per message, with product components only. A replay returns the command's historical outcome; a fresh day query retrieves current totals. Ambiguous external sends require later explicit recovery. These boundaries are documented in the brief and decisions.

## Next action

Independent QA should review this snapshot against [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F), derive its own checks, and record a separate verdict. Keep W001 in QA and M1 in progress until that review and any required fixes are complete.

Closeout update, 2026-09-22: the subsequent independent review passed; see [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F). The statements above preserve the developer handoff's status at execution time. Current task/milestone status belongs to the brief/roadmap.
