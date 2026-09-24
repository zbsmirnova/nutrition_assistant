# W022 — Local recipe provisioning for the MVP pilot

Status: done.
Milestone: M3 pilot setup.
Owner: lead assistant, architect/developer.
Decision: D037.

## Outcome and scope

Add a trusted local operator command that creates one owner-scoped recipe with
explicit per-100-g nutrition. The command may retain an optional JSON list of
ingredient snapshots and cooking instructions so a saved recipe can be tested
through Telegram without allowing the model to create or mutate catalog data.

This is pilot setup only. Natural-language recipe definition, product lookup,
external comparison, aliases, and user-facing catalog editing remain outside
this slice.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W022-A01 | `recipe-create` requires an owner UUID, name, and at least one supplied nutrition value, then creates an owner-scoped immutable recipe version. |
| W022-A02 | Optional ingredient JSON is validated and retained as original snapshots; its sources remain explicitly unresolved rather than being guessed. |
| W022-A03 | The recipe version is pinned to an `operator_catalog` source and the command performs no provider or external-catalog call. |
| W022-A04 | Malformed ingredients and empty/invalid nutrition are rejected before mutation. |
| W022-A05 | Existing recipe consumption, worker, Telegram, and migration behavior remains unchanged. |

## Usage

```sh
.venv/bin/python -m nutrition_app recipe-create \
  --user "$INTERNAL_USER_ID" \
  --name "Овсяная каша" \
  --kcal 76 --protein-g 2.5 --fat-g 1.2 --carbs-g 13 \
  --ingredients-json '[
    {"name":"Овсяные хлопья","amount":"93","unit":"g","weight_basis":"raw"},
    {"name":"Вода","amount":"375","unit":"ml"}
  ]'
```

Nutrition values are entered per 100 g. The command returns `recipe_id` and
`version_id`; subsequent Telegram food messages must still state the eaten
grams explicitly.

## Verification

Developer verification: 116 offline tests, 99 PostgreSQL integration tests,
32 retained QA tests, and `git diff --check` passed on 2026-09-24. The new
recipe provisioning path is covered by two integration tests. No independent
W022 review or live Telegram recipe result is claimed yet; the retained QA run
is evidence for previously reviewed slices.
