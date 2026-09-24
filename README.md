# Nutrition assistant

A personal Telegram assistant for conversational food logging, recipes, daily body weight, and steps. The planned chat language is Russian, with Europe/Berlin as the initial time zone. Food is saved continuously and steps are recorded independently; close-day and reminder check-ins are post-MVP work.

## Current stage

The local persistence service saves resolved food commands with deterministic totals and safe retries. W002 adds private Telegram ingestion, durable polling, account linking, Russian response rendering, and bot-scoped delivery. Its verification uses synthetic Telegram responses and real local PostgreSQL; no real bot messages have been sent.

M1 completed on 2026-09-22. Verification passed: 41 contract/arithmetic tests, 26 PostgreSQL integration tests, and 10 additional independently authored QA checks. Independent QA passed the local persistence scope; database execution was assisted by the lead. The completed brief is [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F), with evidence in [001-persist-food-entry-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/001-persist-food-entry-qa.md?type=file&root=%252F). The current implementation checks pass at 116 offline tests, 102 PostgreSQL integration tests, and 32 retained QA checks; these later totals include developer-verified slices and do not constitute an independent review of each one.

Completed slices include [017-daily-observations.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/017-daily-observations.md?type=file&root=%252F), which adds one revisable weight and steps value per day. [018-combined-check-in.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/018-combined-check-in.md?type=file&root=%252F) is now planned post-MVP and will combine the future dinner trigger with scheduled reminders; [019-scheduled-check-in-reminders.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/019-scheduled-check-in-reminders.md?type=file&root=%252F) is merged into that W018 scope. Earlier slices [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F) through [016-approved-estimated-portion.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/016-approved-estimated-portion.md?type=file&root=%252F) provide the food, recipe, correction, transport, and user-approved-estimate foundations. W002 and W003 passed independent review within their synthetic scope; later slices have developer verification only. W004 adds an explicit Nebius adapter, independently reviewed with injected responses; live compatibility and quality remain unverified. Deployment remains future work. The local CLI is a trusted operator interface, with explicitly provisioned Telegram accounts.

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

Apply the current migration head before using these commands (`migrate` handles this; the current head includes daily observations). No new runtime dependencies are needed. The API adapter uses normal HTTPS certificate verification; if your environment uses a custom CA, configure its trusted CA through Python's standard SSL_CERT_FILE setting.

The local transport harness is verified with synthetic data. The selected model provider is Nebius Token Factory; real-message retention and other data-lifecycle details remain open. These commands are documented for explicit operator use; they are not run by the test suite. Configure NUTRITION_TELEGRAM_TOKEN and NUTRITION_TELEGRAM_BOT_ID in your local environment; do not place a token in a command argument, chat message, or repository file.

Create an owner with `user-create`, then copy the `user_id` from its JSON output. The uppercase values below are placeholders and must not be typed literally: `INTERNAL_USER_UUID` is a UUID, while the Telegram bot, user, and private-chat IDs are positive integers. For a private one-to-one chat, Telegram's chat ID is normally the same numeric value as your Telegram user ID. Obtain your Telegram user ID through your own Telegram account; never put the bot token in a command or repository file.

~~~sh
.venv/bin/python -m nutrition_app migrate
.venv/bin/python -m nutrition_app user-create --time-zone Europe/Berlin
.venv/bin/python -m nutrition_app product-create --user INTERNAL_USER_UUID --name "Яблоко" --kcal 52 --protein-g 0.3 --fat-g 0.2 --carbs-g 14
.venv/bin/python -m nutrition_app recipe-create --user INTERNAL_USER_UUID --name "Овсяная каша" --kcal 76 --protein-g 2.5 --fat-g 1.2 --carbs-g 13
.venv/bin/python -m nutrition_app telegram-link --user INTERNAL_USER_UUID --bot-id BOT_ID --telegram-user-id TELEGRAM_USER_ID --chat-id PRIVATE_CHAT_ID
.venv/bin/python -m nutrition_app telegram-poll --timeout 25
.venv/bin/python -m nutrition_app telegram-send
.venv/bin/python -m nutrition_app telegram-process --user INTERNAL_USER_UUID --timeout 25
~~~

Each poll command receives one batch into the durable inbox; it does not run a parser or create food entries. Each send command attempts one committed food response for the configured bot. Repeated invocations resume from persisted state. The separate conversation worker below connects synthetic interpretation to validated commands. Existing fake dispatch remains available for synthetic demos.

The `product-create` line is trusted local pilot setup: replace the example name and nutrition with values from your product label. It creates an owner-scoped catalog version; it does not call Nebius or let the model invent nutrition. Use it before sending a matching food message through Telegram. See [W021](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/021-local-catalog-provisioning.md?type=file&root=%252F).

The `recipe-create` line is the corresponding trusted setup for a saved recipe. It records explicit per-100-g nutrition and does not calculate or infer nutrition from ingredient names. Add `--ingredients-json` when the original ingredient snapshots should be retained. A later Telegram message must include the grams eaten; no default serving is created. See [W022](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/022-local-recipe-provisioning.md?type=file&root=%252F).

For the fastest personal pilot, `telegram-process` composes those steps once: it polls one bounded batch, processes the oldest eligible message for the supplied owner through the configured Nebius parser, and sends one queued response. Repeat it for the next message. Its output reports only poll, processing, and delivery status; it does not print message text or food totals. It is an operator command, not a daemon or scheduler. See [W020](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/020-telegram-processing-loop.md?type=file&root=%252F).

The adapter refuses an active webhook without changing it. Unknown accounts, groups, bot senders, edited messages, and non-text updates create no food. Reply references and forwarding indicators are preserved for later interpretation. Failed and uncertain sends remain in the outbox for explicit investigation; uncertain sends are not automatically repeated. A 429 response defers retry according to retry_after, with at most three proven-unsent attempts.

## Synthetic conversation worker

~~~sh
.venv/bin/python -m nutrition_app migrate
.venv/bin/python -m nutrition_app conversation-demo
~~~

The demo creates a separate fixed synthetic owner/catalog, ingests “Съела 100 г творога 5% «Марка А»” through the Telegram normalization boundary, consumes a controlled parser response, saves one entry, and renders/delivers its reply to a fake Telegram API. Its supplied synthetic profile gives **120 kcal, 16 g protein, 5 g fat, and 3 g carbohydrate** for the 100 g entry. Repeating the demo preserves one entry and sends no second reply. It does not call Nebius or Telegram.

For explicit operator exercises, prepare a JSON fixture with source_text, ordered candidate_names, and output matching the existing ParserOutput schema. The fixture must match the source and catalog exactly. The demo's fixture helper illustrates this format. Replace the uppercase placeholders:

~~~sh
.venv/bin/python -m nutrition_app conversation-run --user INTERNAL_USER_UUID --source INBOX_UUID --fixture SYNTHETIC_FIXTURE_JSON
.venv/bin/python -m nutrition_app conversation-status --user INTERNAL_USER_UUID
~~~

The run command processes one identified input; repeat it to resume eligible work. It reuses a frozen command without another parse. Status shows received, processing, retry, applied, unresolved, unsupported, rejected, or failed work without printing message text. Retry delays and limits persist; terminal failed/deferred work needs later explicit resolution, not a silent automatic reparse. Optional --crash checkpoints are for disposable local crash tests only.

The resolver currently supports one product or saved recipe with explicit grams and supported date/basis, plus W009/W010's bounded reply/candidate/unique-description targets, numbered selection, one-component quantity correction, date move, meal change, delete, and undo. New catalog versions need an explicit food_kind (general or dairy); dairy identity can include declared_fat_percent. Migration preserves legacy unknown classification, so new interpretations wait for classified versions instead of guessing. Existing prepared commands continue to work. Missing dairy percentage stays unresolved until a reply to the original Telegram message supplies the typed fat answer; the worker then reuses the original quantity/date and operation once. Unresolved food with a known date appears in that day's pending count until the answer is applied. Recipe names auto-select only a unique current owned match; duplicate or absent names stay unresolved, while an explicit scoped recipe candidate may select one version. Multi-component corrections, arbitrary target search, aliases/inflection, and general quantity clarifications remain future slices. See D011, D015, D018, D019, and D023 for context limits and pending-state rules.

## Nebius provider setup

The user selected Nebius Token Factory cloud inference and will supply an API key as a secret. Expose that secret to the application process as NEBIUS_API_KEY. The exact model ID will use NUTRITION_LLM_MODEL; model selection follows evaluation rather than an assumed default. The non-secret [.env.example](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/.env.example?type=file&root=%252F) records these names. The application does not automatically load .env files. The user has reported a live response that passed schema/reference validation but failed the expected food-action check; a successful live smoke result remains pending.

Nebius's documented API base is https://api.tokenfactory.nebius.com/v1/. The worker and offline provider checks run without credentials. Supplying the secret will not automatically run inference, process stored messages, or deploy the application. The provider decision, official references, and remaining evaluation requirements are in [0009-nebius-cloud-provider.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0009-nebius-cloud-provider.md?type=file&root=%252F).

After configuring the two environment variables through your secret mechanism, an explicit synthetic check is available:

~~~sh
.venv/bin/python -m nutrition_app nebius-smoke
~~~

This sends one fixed synthetic dairy entry to Nebius, validates the returned action through the existing resolver, and prints validation flags plus a parser fingerprint. It never opens the database and does not print the source, response or key. A user-run live smoke passed on 2026-09-24 with parser fingerprint `nebius:8776352673608f0fdef39ea5d7cebfc8336e2056454cff9c4de166a9e643cd3d`. This confirms one synthetic model path only; it is not a general food-quality or Telegram-readiness result. A separate user-run pilot later saved one provisioned product and delivered its response; this remains one end-to-end example, not a quality verdict.

The production parser now omits model-authored evidence. It derives the original source text in the backend only after the provider proposal passes its strict schema and parser-context checks; the internal command contract still retains explicit evidence provenance. Use the production prompt and contract for both evaluation and `conversation-nebius`:

~~~sh
NUTRITION_LLM_MODEL='MiniMaxAI/MiniMax-M3' SSL_CERT_FILE=/etc/ssl/cert.pem \
.venv/bin/python -m evals.run_interpretation_eval --parser nebius \
  --prompt evals/prompt_candidate_v5.txt --case INTAKE-002
~~~

The former `--diagnostic-no-evidence` path remains an evaluation comparison only; it is no longer needed for the production worker. D033 records the boundary and its rationale.

### macOS certificate setup

If nebius-smoke returns `parser_unavailable` with `Nebius request unavailable`, the HTTPS request raised an exception. This message alone does not distinguish a certificate failure from a timeout or another connection problem. On this development Mac, Python 3.14's default CA file was missing, and a separate request reproduced `SSLCertVerificationError: unable to get local issuer certificate`. Using the existing macOS CA bundle fixed that connection while retaining certificate verification:

~~~sh
export SSL_CERT_FILE=/etc/ssl/cert.pem
.venv/bin/python -m nutrition_app nebius-smoke
~~~

Run these commands in the same terminal where NEBIUS_API_KEY and NUTRITION_LLM_MODEL are exported. SSL_CERT_FILE lasts for that shell session and its child processes; no credentials need to be re-entered or written to a file. Use this setting only where that CA bundle exists and is appropriate for the environment.

Developer connectivity check on 2026-09-23: the application's Python interpreter, with this setting and default HTTPS verification, reached GET /v1/models and received HTTP 401, as expected without authentication. No API key, food input, or inference request was sent. This confirms HTTPS connectivity only; authenticated model/schema compatibility remains unverified.

If the smoke check reports `parser_rejected` with `Nebius rejected the request (HTTP NNN)`, share that diagnostic to identify the provider's status before changing credentials or the request schema. An older message without the HTTP number cannot distinguish these causes; rerun with the current code in the same configured terminal. The diagnostic exposes only the numeric status, not the provider's error body, headers, or API key. The status narrows investigation but does not prove the exact cause.

For HTTP 401, resolve authentication first: copy the complete secret value from [Nebius Token Factory API keys](https://tokenfactory.nebius.com/project/api-keys), creating a new key if the original value is unavailable. The value is displayed only at creation, according to [Nebius authentication instructions](https://docs.tokenfactory.nebius.com/api-reference/introduction#authentication). Supply only that value as NEBIUS_API_KEY, without quotes or a Bearer prefix; the adapter adds the prefix. Read it into the same shell with `read -rs 'NEBIUS_API_KEY?Paste API key, then press Enter: '`, paste the key when prompted, then run `echo` and `export NEBIUS_API_KEY` separately. Keep the model setting unchanged and rerun the smoke command. Never put the secret itself in command history, a repository file or chat. A 401 does not yet establish model or schema compatibility.

The read command deliberately displays no characters while you paste. Press Enter after pasting the secret; text following `?` in the command is just the prompt, not the key's value.

Dates follow a backend-owned rule: the model can quote date words from the message, but it cannot invent the target date. An undated food message uses its source timestamp converted to the user's time zone; explicit supported date phrases are resolved by the backend, and ambiguous phrases stay pending.

For HTTP 422, investigate request validation rather than re-entering the key. The current adapter uses the named schema wrapper required by Nebius's published API and the production proposal schema without model-authored evidence. That request shape is checked against the provider's OpenAPI definitions, but successful inference with the configured model remains unverified. Retry the smoke command in the same configured terminal. The provider contract/prompt change changes parser identity for unfinished worker jobs; already frozen commands retain their existing recovery path.

If the error says "Synthetic smoke response did not match the expected food action", the completion already passed schema/reference validation. The diagnostic includes validated action kinds, backend resolution/reason codes and safe unresolved-field names. Share that diagnostic; the check never prints raw model text or credentials. The smoke comparison treats equivalent decimal quantities such as 100 and 100.0 as equal. It still rejects different quantities, unresolved food and wrong actions.

### Processing an explicit inbox source

For an explicit identified inbox source, the operator command is:

~~~sh
.venv/bin/python -m nutrition_app conversation-nebius --user INTERNAL_USER_UUID --source INBOX_UUID
~~~

This command sends source text/date/time zone and bounded public product context to Nebius, then applies W003's validation, dairy/quantity/date guards, authorization, arithmetic and idempotency. It does not poll, send Telegram replies, or process the whole inbox. Real-data lifecycle choices remain Q10; start live verification with the synthetic check. Existing conversation-run remains the controlled-fixture path. Model/prompt/schema changes fence unfinished work; key rotation preserves parser identity. Frozen commands resume without another model call. An unresolved live food message is held without a food mutation; this runtime slice does not yet enqueue a Telegram clarification for `product_unresolved`.

Transient failures retry through durable job state, with three total claims and valid Retry-After delays. Permanent provider errors or invalid output become visible failed jobs without food. Terminal recovery after correcting configuration is later explicit tooling. Requests use the fixed HTTPS endpoint, verified TLS, a 30-second socket timeout and 256-KiB size limits; no redirect, provider fallback, schema downgrade or hidden retry occurs. D012 and [004-nebius-adapter.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F) record scope and review status.

## Verification

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
.venv/bin/python -m pip check
git diff --check
~~~

The first command currently runs 110 offline checks, including exact-weight clarification and approved-estimate provenance. The integration command runs 81 tests against local PostgreSQL, including clarification resumption, mixed partial saving, pinned recipe consumption, recipe clarification, and approved-estimate persistence; the separate QA command runs 32 retained checks from M1, W002, W003, and W004. Developer verification and independent review are distinguished in the work briefs and QA reports. Each database test creates and removes its own randomly named schema. These commands do not reset development data or call Telegram/Nebius. An unavailable database fails the run; there is no silent skip or SQLite substitute.

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
