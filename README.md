# Nutrition assistant

A personal Telegram assistant for conversational food logging, recipes, daily body weight, and steps. The planned chat language is Russian, with Europe/Berlin as the initial time zone. Food is saved continuously; the optional daily check-in records completeness and invites missing activity.

## Current stage

The first local persistence slice is implemented: PostgreSQL migrations, owned seeded product data, deterministic food/day totals, stable prepared commands, atomic changes/results/reply intent, and a fake delivery adapter. Typed contracts and 20 authored parser scenarios remain the foundation for later conversation work.

Developer verification on 2026-09-22: 41 contract/arithmetic tests and 26 PostgreSQL integration tests passed, including real process crashes and concurrent requests. Independent QA passed this local persistence scope (with lead-assisted database execution); the current work brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F).

There is no live Telegram ingress, LLM parser/resolver, correction workflow, recipe engine, daily-observation service, scheduler, or deployed nutrition application yet. The local CLI accepts resolved commands as a trusted development operator; it is not a public authentication interface.

## Run the synthetic local demo

Requires Docker Compose and Python 3.12+; Python 3.14.0 is the verified interpreter. Commands run from the repository root.

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
docker compose -f compose.dev.yml up -d --wait db
.venv/bin/python -m nutrition_app migrate
.venv/bin/python -m nutrition_app demo
~~~

The demo uses a fixed synthetic message dated 2026-09-22: 250 g at 100 kcal / 4 g protein / 4 g fat / 12 g carbohydrate per 100 g. Expect **250 kcal, 10 g protein, 10 g fat, 30 g carbohydrate** and one entry. Repeating the demo reuses its message/operation and does not add another portion.

[compose.dev.yml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/compose.dev.yml?type=file&root=%252F) pins PostgreSQL 17.11's image digest and binds the database to localhost port 55432. Credentials are deliberately public local-development values. Data lives in the named Docker volume. The application's default URL points only to this local database; an explicit NUTRITION_DATABASE_URL can override it.

~~~sh
.venv/bin/python -m nutrition_app dispatch
.venv/bin/python -m nutrition_app db-info
~~~

Dispatch uses an in-memory fake and marks one committed response as sent; it never contacts Telegram. A second dispatch is idle if no pending responses remain. An ambiguous send or expired claim becomes uncertain rather than being blindly repeated. Manual resolution of uncertain sends belongs to the future real-transport adapter.

To stop local PostgreSQL while preserving its volume:

~~~sh
docker compose -f compose.dev.yml stop db
~~~

## Verification

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
.venv/bin/python -m pip check
git diff --check
~~~

The first command runs the 32 contract tests plus 9 arithmetic tests. The QA command runs 10 retained independent checks. The explicit integration command runs 26 additional tests against local PostgreSQL; each creates and removes its own randomly named schema. It does not reset development data. An unavailable database fails the integration run; there is no silent skip or SQLite substitute.

Runtime dependencies are pinned in [requirements-runtime.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/requirements-runtime.txt?type=file&root=%252F), including [requirements-contracts.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/requirements-contracts.txt?type=file&root=%252F). For contract-only work, install the latter and run unittest discovery with the pattern test_contracts.py. No provider credentials are needed.

After changing contract models, regenerate schemas and run the relevant checks:

~~~sh
.venv/bin/python -m nutrition_contracts.export
~~~

Alembic revisions are the migration history. The runtime model in [schema.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/schema.py?type=file&root=%252F) supports queries and drift checks; migrations do not import it to recreate historical schemas.

## Project documents

| Document | Purpose |
| --- | --- |
| [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F) | Product goals, scope, and enduring requirements. |
| [AGENTS.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/AGENTS.md?type=file&root=%252F) | Agent/contributor instructions and maintenance responsibility. |
| [architecture-plan.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/architecture-plan.md?type=file&root=%252F) | System boundaries and current design. |
| [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F) | Full logical model and the implemented M1 subset. |
| [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F) | Interaction rules and proposed edge-case defaults. |
| [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F) | Contracts, authored examples, and validation limits. |
| [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F) | Decision history and the single question register. |
| [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F) | Milestones and exit criteria. |
| [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F) | Independent verification and evidence requirements. |
| [development-process.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/development-process.md?type=file&root=%252F) | Workflow and document ownership. |

[Dockerfile](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/Dockerfile?type=file&root=%252F) and [fly.toml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/fly.toml?type=file&root=%252F) still describe the existing Open WebUI deployment context. They do not deploy this application. Hosting and real-data provider/privacy requirements remain open.
