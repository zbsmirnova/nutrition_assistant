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
| MVP-CLR | `test_conversation_worker` clarification/resume/estimate cases | PASS для pending contract; модельные формулировки — MODEL-EVAL |
| MVP-COR-01..08 | correction, bot reply, ambiguity, date/meal tests | PASS |
| MVP-COR-09..21 | add/subtract, reply delete, bot acknowledgment, latest delete, empty log, replay | PASS |
| MVP-NEG | non-logging, unsupported, unknown and invalid proposal tests | PASS for no-mutation guards |
| MVP-TXT | contract and resolver boundary tests | PARTIAL: controlled parser does not prove typo/abbreviation recognition |
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

## Verdict boundary

The local MVP persistence and worker checklist is covered by executable tests.
The suite cannot claim full natural-language coverage, live Nebius quality, or
real Telegram transport until those environments are exercised separately.
