# QA report — W011 / developer verification

## Identity and scope

Date: 2026-09-23
Reviewer and role: lead assistant, developer verification
Work brief: [011-recipe-persistence.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/011-recipe-persistence.md?type=file&root=%252F)
Review type: developer verification
Implementation commit: [643e66d](air-commit://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant?commit=643e66d62eaacc45b035d317d911b709da186663&root=%252F)

## Checks and evidence

| Criterion | Evidence | Result |
| --- | --- | --- |
| W011-A01 definition persistence | `test_define_recipe_persists_original_ingredients_and_profile` | Recipe identity, version, instructions, per-100-g profile, and original quantities persisted and retrieved |
| W011-A02 backend calculation | `test_calculated_recipe_uses_pinned_mass_source_and_preserves_source_snapshot` | Product-version nutrition is calculated in the backend; normalized mass source is retained |
| W011-A03 immutable revision | `test_revision_creates_new_version_and_rejects_stale_revision` | New version created; stale expected version raises conflict |
| W011-A04 ownership/retrieval | Recipe service integration coverage and existing ownership tests | Current version retrieval and tenant-scoped source checks pass |
| W011-A05 regression/migration | `.venv/bin/python -m unittest discover -s tests -q`; `.venv/bin/python -m unittest discover -s tests/integration -q`; `.venv/bin/python -m unittest discover -s tests/qa -q`; `git diff --check` | 96 offline, 73 integration, 32 QA passed; diff check passed |

## Limits and verdict

Verdict: pass for W011's persistence scope. No live Nebius interpretation, recipe conversation, recipe consumption, external general-database comparison, real Telegram delivery, or independent QA review is claimed. Volume ingredients must arrive with normalized mass for calculated profiles; density resolution is a later slice.
