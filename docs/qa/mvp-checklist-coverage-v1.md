# MVP checklist coverage map

Статус: локальное автоматизированное покрытие на ветке `mvp_qa`.

Чеклист разделен по типу доказательства. Интеграционные тесты проверяют
сохранение, revisions, totals, pending state, owner isolation, retry и
идемпотентность. Unit/contract тесты проверяют wire-контракт и безопасные
границы. Русские формулировки, сокращения и опечатки требуют отдельной оценки
качества интерпретатора; controlled parser не доказывает качество живой модели.

| Группа чеклиста | Автоматизированное покрытие | Статус |
| --- | --- | --- |
| MVP-IN | `test_conversation_worker`, `test_food_service` | PASS для persistence и delivery identity; живые формулировки — MODEL-EVAL |
| MVP-REC | `test_conversation_worker` recipe cases, `test_food_service` version pinning | PASS для поддержанного recipe path |
| MVP-CLR | `test_conversation_worker` clarification/resume/estimate/cancellation cases | PASS для pending contract, restart, cancellation и unrelated observation isolation; модельные формулировки — MODEL-EVAL |
| MVP-COR-01..08 | correction, bot reply, ambiguity, date/meal tests | PASS |
| MVP-COR-09..21 | set/add/subtract, safe half deferral, user/bot reply delete, named/current-day delete, ambiguity, latest delete, empty log, replay | PASS |
| MVP-NEG | non-logging, unsupported, unknown and invalid proposal tests | PASS for no-mutation guards |
| MVP-TXT | resolver boundary tests for unit spellings, compact input, punctuation, typo, word quantity and two-quantity input | PASS for backend acceptance/safe deferral; live recognition remains MODEL-EVAL |
| MVP-REL | crash, retry, competing worker, outbox and duplicate delivery tests | PASS |
| MVP-OBS | `test_observation_service` weight/steps/date/zero/idempotency cases | PASS |

## Explicit latest-delete coverage

- `Удали последнее`, `удалить последнюю запись`, `убери последнюю еду`,
  `сотри последнюю порцию`, `стереть последний прием` are checked by
  `tests/test_conversation_commands.py`.
- The worker handles an exact standalone latest-delete before the provider
  parser; integration tests prove that no parser call is made.
- The latest active entry is deleted once, replay is idempotent, and an empty
  log returns `entry_target_not_found` without a mutation.
- Reply to the user's food message and reply to the bot acknowledgment remain
  separate covered paths.

## Follow-up correction and clarification coverage

- `Сделай 80 г` and `Было 80 г` replace the quantity on the same entry;
  `Еще 50 грамм` adds a delta; `Половину убери` remains unresolved without an
  invented numeric rule.
- `Удали` is a latest-entry command only without reply context. In reply to a
  user food message or bot acknowledgment it deletes that linked entry, and a
  replay cannot delete another entry.
- When an active food clarification exists, it takes precedence over standalone
  `Удали`: the worker exposes the pending context to the parser and never
  synthesizes a latest-entry deletion. A successful cancellation preserves
  saved entries/totals and queues a visible confirmation exactly once.
- A pending food clarification survives worker recreation, can be explicitly
  cancelled without a food mutation, and is not consumed by a separate weight
  observation.
- Controlled resolver checks accept supported compact gram spellings and
  punctuation. Kilogram conversion, word-number parsing, typos and conflicting
  quantities fail safely when the proposal cannot be verified. These checks do
  not establish that a live model will produce the expected proposal.

## Verdict boundary

The local MVP persistence and worker checklist is covered by executable tests
for the bounded scenarios above. Telegram recipe authoring without finished
yield remains outside the current conversational implementation; recipe
consumption without known grams, recipe version pinning, and product version
pinning are covered. The suite cannot claim full natural-language coverage,
live Nebius quality, or real Telegram transport until those environments are
exercised separately.
