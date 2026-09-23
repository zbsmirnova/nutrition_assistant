# QA report — W012 / developer verification

## Identity and scope

Date: 2026-09-23
Reviewer and role: lead assistant, developer verification
Work brief: [012-recipe-consumption.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/012-recipe-consumption.md?type=file&root=%252F)
Review type: developer verification
Implementation commit: [02febb8](air-commit://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant?commit=02febb850b96f284d57461f4b3d352e0a5f9834e&root=%252F)

## Checks and evidence

| Criterion | Evidence | Result |
| --- | --- | --- |
| W012-A01 consumption | `test_consumption_pins_recipe_version_and_survives_recipe_revision` | Eaten grams create a food entry and daily nutrition from the selected recipe version |
| W012-A02 explicit source kind | Same integration test and migration/schema comparison | Recipe component stores recipe source, no product source, and mass grams |
| W012-A03 historical pinning | Same integration test | A later recipe version changes future food only; the earlier meal remains at 175 kcal |
| W012-A04 invalid/retry behavior | Existing ownership, command, and idempotency suites | Foreign/missing references and retries remain guarded |
| W012-A05 regression/migration | `.venv/bin/python -m unittest discover -s tests -q`; `.venv/bin/python -m unittest discover -s tests/integration -q`; `.venv/bin/python -m unittest discover -s tests/qa -q`; `git diff --check` | 96 offline, 74 integration, 32 QA passed; diff check passed |

## Limits and verdict

Verdict: pass for W012's explicit recipe-consumption scope. No live Nebius interpretation, natural-language recipe lookup, recipe clarification, recipe-aware conversational correction, external comparison, real Telegram delivery, or independent QA review is claimed.
