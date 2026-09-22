# W002 developer verification — attempt 1

Date: 2026-09-22. Reviewer: lead assistant acting as developer.
Verdict: developer checks pass for W002; independent review pending.

## Revision and environment

Base commit: 0500e9918dad269d5e74ff11f13c05fedb55af83. The working tree contains uncommitted M1 and W002 files; the base commit alone does not identify the reviewed source. No staging or commit was created.

Frozen source ID: 8cae828c2e8fe22c956dbb35a34236e530cf8591545d3233d63c67543cce4a0f.
Attempt 1 manifest: [002-source-manifest-attempt1.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-source-manifest-attempt1.json?type=file&root=%252F), 82 files.
Archive: [w002-8cae828c2e8f.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-8cae828c2e8f.tar.gz?type=file&root=%252F).
Archive SHA-256: 1b943f03f29c46daf6079c2fe2cc98f63c5d4632020e67132311f68c9e0c437f.

The archive contains application/contracts/migrations/tests/configuration and governing documents. QA reports/logs, the virtual environment, IDE files, credentials, and legacy deployment configuration are excluded. Evidence files are retained separately so they cannot recursively affect their source identifier. Raw log endings are preserved; the Git attributes exclude only final blank-line warnings for output logs.

Python 3.14.0; existing pinned runtime dependencies unchanged. Local PostgreSQL 17.11, migration head 0003. Data and Telegram responses are synthetic. No model call, actual Telegram send, or credential inspection was performed.

## Commands and observed results

| Command / check | Result |
| --- | --- |
| .venv/bin/python -m unittest discover -s tests -v | 52 passed in 0.395 s: 32 contracts, 9 arithmetic, 11 Telegram protocol/rendering checks. |
| .venv/bin/python -m unittest discover -s tests/integration -v | 38 passed in 13.156 s: 26 food persistence and 12 transport integration checks. |
| .venv/bin/python -m unittest discover -s tests/qa -v | 10 retained M1 probes passed in 2.420 s. This developer execution is not a new independent verdict. |
| Local migrate, followed by demo | Head applied; the pre-existing synthetic M1 source/result replayed successfully. One entry remained, with 250 kcal / 10 g protein / 10 g fat / 30 g carbohydrate. |
| pip check; git diff --check | No broken dependencies; formatting passed. |
| CLI help and Python compilation | Passed. No live transport command executed. |

Raw logs: [002-developer-unit-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-developer-unit-output.txt?type=file&root=%252F), [002-developer-integration-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-developer-integration-output.txt?type=file&root=%252F), [002-developer-retained-qa-output.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-developer-retained-qa-output.txt?type=file&root=%252F).

## Acceptance coverage

| Criterion | Developer evidence |
| --- | --- |
| W002-A01 | Private account mapping; unknown sender, group, bot, media and edited updates rejected/ignored with no inbox or food records; provisioned identity cannot be reassigned. |
| W002-A02 | Source instant/timezone, reply reference and forwarding flag survive repeated ingestion. A user_id claim in text cannot change the owner. |
| W002-A03 | Real child-process exit after inbox commit leaves cursor unchanged; another process reuses the same source and checkpoints once. Competing poller performs no API call while the first owns the bot lock. New identical-text messages stay distinct. |
| W002-A04 | Legacy hash test, populated 0002→0003 upgrade/replay, full migration/model comparison and retained M1 migration probes pass. The existing public synthetic demo also replays after upgrade. |
| W002-A05 | Full synthetic ingress→fixture command→committed outbox→sender path returns the saved 250 kcal and stores receipt 9001. Another bot's responses and expired claims are untouched. |
| W002-A06 | Russian date-labelled entry/day text, historical-result wording, known zero versus unknown/partial values, bounded multiline Unicode label, no parse mode, and disabled link previews verified. |
| W002-A07 | Explicit rejection becomes failed; 429 waits the supplied delay and respects the three-attempt bound. Server/network/malformed-receipt ambiguity is uncertain. Errors exclude the token and server description. |
| W002-A08 | Token/bot mismatch and existing webhook rejected without deleting configuration. CLI help/setup documented; tests use injected synthetic responses. |

Checks are developer-authored except the retained M1 probes. Independent W002 review must assess this frozen revision and add requirement-derived checks as appropriate.

## Resolved findings and limits

An initial new migration test compared a canonical UTC source hash against a JSON timestamp with a different textual representation. Its expectation was corrected to the existing M1 canonical ISO representation; the complete integration suite then passed. This did not require changing saved hashes or application behavior.

Transport is implemented, but it does not interpret inbox text, schedule a processing worker, or make an app ready for personal use. The end-to-end test explicitly supplies a resolved fixture command. Parser provider/local-model preference and permitted real-message context remain unresolved. No live HTTP service, model, Telegram account, actual Telegram delivery, public onboarding, edited-message workflow, or production deployment was verified. Invalid supported updates stop cursor advancement for investigation rather than silently dropping their text. Operational supervision, outage behavior, and recovery UI remain later work.

Independent QA and subsequent status updates must be recorded separately. The historical M1 report/manifest remains evidence for its original revision; W002 does not rewrite that evidence.

## Attempt 2 — receipt-validation fix

Independent QA reproduced a malformed receipt where boolean True or floating-point 1.0 compared equal to intended chat ID 1. The API adapter now requires a strict positive integer chat ID before accepting equality. The existing protocol test additionally covers boolean, float, and string chat IDs. No database or migration implementation changed.

New source ID: 4ba4769b0cddba32ece9d2b001011ce51ef7614c694d5964c19c22b1c30f2ba2. Current manifest: [002-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-source-manifest.json?type=file&root=%252F).
Archive: [w002-4ba4769b0cdd.tar.gz](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/artifacts/qa/w002-4ba4769b0cdd.tar.gz?type=file&root=%252F), SHA-256 dfdca2d2eade182f1c7b3c0d82d475f847d301ef7781f1f46e0ae8c0ab626963.

Five files changed from attempt 1: the adapter guard, its protocol test, and three documentation updates correcting transport status/linking the handoff. The lead reran all 52 unit/protocol checks: passed in 0.398 s, exit 0. The attempt-1 database results above remain evidence for the unchanged database paths, with revision attribution preserved. Independent targeted recheck is recorded in the separate QA report when complete.

Closeout: [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F) records the independent attempt-2 pass and resolved finding. Six additional retained QA checks also passed from their repository location. W002 is complete; M2 interpretation/conversation work remains. Earlier pending-review statements above preserve the handoff's status at execution time.
