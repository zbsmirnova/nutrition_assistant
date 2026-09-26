# QA-055 — MVP checklist correction, deletion, and clarification slices

Status: passed for the covered slice.
Date: 2026-09-26.
Role: QA verification by the lead assistant.

## Revision and evidence

- Base commit: `b40c368` (`mvp_qa`).
- Working-tree patch SHA-256 (excluding this report): `974ca1894d19932446bc0bca0185296ec263b0d19a4dd7957e6b4f04449a8681`.
- Runtime: project `.venv`, Python 3.14, local PostgreSQL 17.11 disposable schemas.
- Migration head: current project head used by the integration fixtures.
- No live Telegram or Nebius request was used.

## Covered behavior

The worker recognizes bounded standalone delete wording before the provider
parser and builds a `latest` delete action. The latest active entry is selected
from the backend ordered context; an empty log returns
`entry_target_not_found` without a mutation. Reply deletion, bot acknowledgment
deletion, candidate deletion and undo remain covered.

The same slice covers explicit quantity adjustments: `Добавь еще 30 г` and
`Убавь 20 г` revise the existing entry, while a non-positive result is rejected
without a domain mutation.

## Full verification

| Suite | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | 132 passed |
| `.venv/bin/python -m unittest discover -s tests/integration -v` | 114 passed |
| `.venv/bin/python -m unittest discover -s tests/qa -v` | 32 passed |
| `git diff --check` | passed |

## Limits

This verifies controlled parser proposals and local persistence/worker
behavior. It does not establish live Russian-language model quality or real
Telegram delivery. Abbreviation and typo quality remains MODEL-EVAL.

## Follow-up verification attempt

Status: developer verification passed for the expanded checklist slice.
Date: 2026-09-26.

- Base commit: `2b6415f` (`mvp_qa`).
- Working-tree patch SHA-256 before this report update:
  `1fd8ff76bff5a5b8b978d1bd6dc9d24e11d97dd8a2d5444d2435040f1411ac58`.
- Runtime: project `.venv`, Python 3.14, local PostgreSQL 17.11 disposable
  schemas; migration head unchanged.
- No live Telegram or Nebius request was used. This is developer verification,
  not a new independent QA review.

The follow-up covers supported gram spellings and compact forms, safe deferral
for word quantities, typos and conflicting quantities, emoji/newline input,
short replacement and delta corrections, nonnumeric half removal, deletion by
reply to the user message and bot acknowledgment, named current-day deletion,
bare/latest deletion, replay idempotency, explicit pending cancellation,
worker-restart resumption, and isolation of an unrelated weight observation.
Existing suites retain product ambiguity, approximate/approved quantities,
recipe portion clarification, and product/recipe version pinning coverage.

| Suite | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | 133 passed |
| `.venv/bin/python -m unittest discover -s tests/integration -v` | 119 passed |
| `.venv/bin/python -m unittest discover -s tests/qa -v` | 32 passed |
| `git diff --check` | passed |

Remaining limits: live-model recognition of abbreviations, typos, word numbers,
punctuation and conversational phrasing is unverified; kilogram-to-gram
conversion and typo correction currently defer rather than mutate; Telegram
recipe authoring without finished yield is not implemented; no live Telegram
transport was executed in this attempt. Provider adapter/worker integration is
covered with injected responses, separate from live model quality.

## D054 pending-precedence recheck

Status: developer verification passed.
Date: 2026-09-26.

The worker no longer synthesizes `delete_food(target=latest)` for a targetless
standalone `Удали` while an active food clarification exists. The bounded
single-pending path supplies that pending context to the parser; a validated
`cancel_clarification` closes it and queues a typed `pending_cancelled` outcome.
The Telegram renderer returns `Уточнение по еде отменено. Ничего не записано.`

The integration regression starts with saved entry E1, opens a clarification
for another food, sends standalone `Удали`, and verifies that E1, its revision,
and its kcal total remain unchanged. It also verifies pending closure, one
durable cancellation outbox item, renderer text, and replay idempotency.
Standalone latest deletion without pending remains covered separately.

Evidence identity:

- Base commit: `94712fd` (`mvp_qa`).
- Working-tree patch SHA-256 excluding this report:
  `4679e607e7cafd762e6dc978f75b06c4578d61cd5fc485113cf3f602f2616283`.
- Migration head unchanged; `outcome.schema.json` was regenerated from the
  Python result model.

| Suite | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | 134 passed |
| `.venv/bin/python -m unittest discover -s tests/integration -v` | 120 passed |
| `.venv/bin/python -m unittest discover -s tests/qa -v` | 32 passed |
| `git diff --check` | passed |

No live Telegram or Nebius request is part of this recheck. This is developer
verification; no new independent QA review was performed.
