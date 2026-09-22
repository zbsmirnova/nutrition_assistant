# Nutrition assistant

A personal Telegram assistant for conversational food logging, recipes, daily body weight, and steps. The planned chat language is Russian, with Europe/Berlin as the initial time zone. Food is saved continuously; the optional daily check-in records completeness and invites missing activity.

## Current stage

The local persistence service saves resolved food commands with deterministic totals and safe retries. W002 adds private Telegram ingestion, durable polling, account linking, Russian response rendering, and bot-scoped delivery. Its verification uses synthetic Telegram responses and real local PostgreSQL; no real bot messages have been sent.

M1 completed on 2026-09-22. Verification passed: 41 contract/arithmetic tests, 26 PostgreSQL integration tests, and 10 additional independently authored QA checks. Independent QA passed the local persistence scope; database execution was assisted by the lead. The completed brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F), with evidence in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F).

Next work: [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F) defines the provider-neutral message-to-food worker, starting with synthetic parser responses. Independent QA passed the completed W002 transport scope after a receipt-validation fix; evidence is in [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F). There is no LLM parser/resolver, conversational correction workflow, recipe engine, daily-observation service, scheduler, or deployed nutrition application yet. Received text is durable inbox input; it is not automatically interpreted or saved as food. The local CLI is a trusted operator interface, with explicitly provisioned Telegram accounts.

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

## Telegram transport development

Apply migration head 0003 before using transport commands. No new runtime dependencies are needed. The API adapter uses normal HTTPS certificate verification; if your environment uses a custom CA, configure its trusted CA through Python's standard SSL_CERT_FILE setting.

The local transport harness is verified with synthetic data. The selected model provider is Nebius Token Factory; real-message retention and other data-lifecycle details remain open. These commands are documented for explicit operator use; they are not run by the test suite. Configure NUTRITION_TELEGRAM_TOKEN and NUTRITION_TELEGRAM_BOT_ID in your local environment; do not place a token in a command argument, chat message, or repository file.

Create an owner with user-create, or use an existing internal user ID. Link that owner to numeric Telegram bot/user/private-chat IDs obtained through your own account. Replace the uppercase placeholders below:

~~~sh
.venv/bin/python -m nutrition_app migrate
.venv/bin/python -m nutrition_app user-create --time-zone Europe/Berlin
.venv/bin/python -m nutrition_app telegram-link --user INTERNAL_USER_UUID --bot-id BOT_ID --telegram-user-id TELEGRAM_USER_ID --chat-id PRIVATE_CHAT_ID
.venv/bin/python -m nutrition_app telegram-poll --timeout 25
.venv/bin/python -m nutrition_app telegram-send
~~~

Each poll command receives one batch into the durable inbox; it does not run a parser or create food entries. Each send command attempts one committed food response for the configured bot. Repeated invocations resume from persisted state. A future conversation worker will interpret inbox messages and produce validated commands. Existing fake dispatch remains available for synthetic demos.

The adapter refuses an active webhook without changing it. Unknown accounts, groups, bot senders, edited messages, and non-text updates create no food. Reply references and forwarding indicators are preserved for later interpretation. Failed and uncertain sends remain in the outbox for explicit investigation; uncertain sends are not automatically repeated. A 429 response defers retry according to retry_after, with at most three proven-unsent attempts.

## Nebius provider setup

The user selected Nebius Token Factory cloud inference and will supply an API key as a secret. Expose that secret to the application process as NEBIUS_API_KEY. The exact model ID will use NUTRITION_LLM_MODEL; model selection follows evaluation rather than an assumed default. The non-secret [.env.example](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/.env.example?type=file&root=%252F) records these names. The application does not automatically load .env files, and no provider adapter or live model call is implemented yet.

Nebius's documented API base is https://api.tokenfactory.nebius.com/v1/. The worker and its synthetic checks can be implemented without credentials. Supplying the secret will not automatically run inference, process stored messages, or deploy the application. The provider decision, official references, and remaining evaluation requirements are in [0009-nebius-cloud-provider.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0009-nebius-cloud-provider.md?type=file&root=%252F).

## Verification

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
.venv/bin/python -m pip check
git diff --check
~~~

The first command runs 52 checks: 32 contract, 9 arithmetic, and 11 Telegram protocol/rendering tests. The integration command runs 38 tests against local PostgreSQL, including 12 transport checks; the separate QA command runs 16 retained checks from M1 and W002. The 106 checks have passing evidence, with revision-specific rechecks documented in the QA reports. Each database test creates and removes its own randomly named schema. These commands do not reset development data or call Telegram. An unavailable database fails the run; there is no silent skip or SQLite substitute.

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

[Dockerfile](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/Dockerfile?type=file&root=%252F) and [fly.toml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/fly.toml?type=file&root=%252F) still describe the existing Open WebUI deployment context. They do not deploy this application. Hosting and remaining data-lifecycle requirements remain open; the Nebius provider choice is accepted.
