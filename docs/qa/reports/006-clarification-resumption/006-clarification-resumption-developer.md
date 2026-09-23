# QA report — W006 / developer verification

## Identity and scope

Date: 2026-09-23
Reviewer and role: lead assistant, developer verification
Work brief and acceptance criteria: [006-clarification-resumption.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/006-clarification-resumption.md?type=file&root=%252F)
Review type: developer verification
Commit SHA: `ed179b5`
Working tree: clean before this evidence-only update
Revision/tree state: implementation and tests were committed as `ed179b5`; this report records the checks run against that revision.
Environment: Python 3.14.0 virtual environment; pinned runtime dependencies; local PostgreSQL 17.11 on the documented port; disposable random PostgreSQL schemas.

## Checks and evidence

| Criterion / scenario | Command or manual steps | Expected | Actual / evidence | Status |
| --- | --- | --- | --- | --- |
| W006-A01 pending state | `python -m unittest discover -s tests/integration -v`; `test_unknown_fat_is_pending_and_visible_in_later_day_totals` | Missing dairy fat creates no food and retains a question | Passed; the new `pending_questions` map is stored and pending food remains outside totals | Passed |
| W006-A02 scoped reply | `test_forward_and_reply_inputs_wait_without_calling_parser` and the new reply-resumption test | Only a reply to the exact pending Telegram message can resume it | Passed; unrelated reply context remains deferred, while the linked reply receives `c1/q1` context | Passed |
| W006-A03 original evidence/date | `tests.test_interpretation.InterpretationTests.test_dairy_fat_answer_reuses_original_date_and_operation_evidence` | Answer adds product evidence without changing 100 g or the source date | Passed; backend command retains the original date and quantity | Passed |
| W006-A04 operation/evidence identity | Same unit test plus PostgreSQL clarification test | Original operation ID, original evidence first, answer second, pending job reference | Passed; command is prepared through the original operation and source chain | Passed |
| W006-A05 replay/recovery | Full integration suite, including crash/recovery and `test_dairy_fat_reply_resumes_original_operation_once` | One entry/outbox result; original pending job clears after success | Passed; 60/60 integration tests | Passed |
| W006-A06 invalid/incomplete proposals | Contract/resolver suite and existing invalid proposal tests | No mutation for invalid answer context or incomplete proposal | Passed; 96/96 offline tests | Passed |
| W006-A07 regressions/migration | Full integration and retained QA suites | Existing behavior and migration model remain valid | Passed; 60/60 integration tests and 32/32 retained QA checks | Passed |

Commands executed:

- `.venv/bin/python -m unittest discover -s tests -q` — 96 passed.
- `.venv/bin/python -m unittest discover -s tests/integration -v` — 60 passed.
- `.venv/bin/python -m unittest discover -s tests/qa -v` — 32 passed.
- `git diff --check` — passed before the implementation commit.

## Defects

No defects found in the bounded W006 scenarios.

## Coverage limits

This is developer verification, not an independent W006 QA review. The checks use controlled parser responses and synthetic catalog/messages. No live Nebius request, real Telegram send, mixed-message partial save, multiple pending questions, quantity clarification, cancellation, or correction/delete/undo was exercised. Those remain later M2 slices. The temporary `conversation_jobs.pending_questions` representation is intentionally limited to one pending dairy clarification; D015 records the normalization follow-up.

## Verdict and rechecks

Verdict: pass for W006's bounded scope.
Blocking findings: none.
Remaining nonblocking findings: independent W006 review and live provider/transport checks are still outstanding.
Next action: continue M2 with mixed-message partial saving, then same-entry correction/delete/undo; keep the live Nebius evaluation separate from protocol evidence.
