# D012 — Explicit Nebius requests and durable provider failure handling

Kind: technical.
Status: accepted for W004 under delegated implementation authority.
Recorded: 2026-09-22.
Decision owner: lead architect/developer.
Authority: the user selected Nebius in D009 and instructed continuing with its adapter after W003.

## Decision

Use the standard-library HTTPS client against the fixed api.tokenfactory.nebius.com origin and /v1/chat/completions path. Send bearer authentication from NEBIUS_API_KEY, require an explicit NUTRITION_LLM_MODEL, and retain certificate verification. No configurable alternate host, redirect following, SDK retry loop, or provider fallback is introduced. No dependencies or migration change.

Request one non-streaming completion with temperature 0 and max_tokens 4096. Use response_format.type=json_schema with a named JSON Schema wrapper as specified in the correction below. The original W004 implementation placed the ParserOutput-generated schema directly in json_schema, following the guide's Python example; that format is superseded. Include the unchanged schema in the system prompt as well. There is no schema simplification, JSON repair, or fallback to arbitrary JSON. Exact chosen-model compatibility remains a live verification task.

The request contains only the source text, source-local date and time zone, and W003's public product candidate fields with scoped tokens. Explicitly project candidate fields again at the adapter boundary. Names and source text are data in a separate user message; the system prompt instructs faithful intent extraction and no invented consumption, identities, quantities or nutrients. These instructions do not establish resistance to every prompt injection or model accuracy; existing local validation/resolution remains mandatory.

Set a 30-second socket timeout and a 256-KiB request/response limit. The timeout is a socket inactivity bound, not a guaranteed end-to-end deadline; W003's database lease fences late results. The adapter closes every connection and never reads an error body. Slow responses can expire a worker lease; operator resumption may repeat an uncommitted inference, so provider billing is not exactly once.

Accept only one index-zero assistant choice ending with stop, nonempty content, no refusal, and no tool/function call. Validate the content against ParserOutput and scoped evidence/references before returning it to W003, which validates/resolves again. Reject malformed envelopes, truncated/refused outputs, invalid JSON/schema/evidence, oversized responses and permanent non-200 statuses. Operational error strings contain no key, model payload, source text, provider body or exception details.

Setup follow-up on 2026-09-23: permanent HTTP rejection diagnostics include the integer HTTP status so operator troubleshooting can distinguish provider responses. Error bodies remain unread; response headers and reason phrases are not printed. This diagnostic-only change preserves request semantics and parser identity.

Transient network errors, HTTP 408/429 and 5xx use the existing durable worker retry budget of three claims. Retry-After supports integer seconds or HTTP dates after normalizing surrounding HTTP spaces/tabs; the stored delay is the greater of the hint and existing exponential backoff. A 429 without a usable hint waits at least 60 seconds. Hints beyond one day stop visibly instead of retrying earlier than instructed. Permanent provider rejection becomes a terminal failed job; no food/outbox mutation occurs. The inbox remains inspectable. Resetting terminal jobs after operator corrections remains later explicit recovery tooling, not silent automatic reprocessing.

The parser version hashes adapter policy, fixed endpoint, timeout/limits, model, system prompt, schema and generation parameters. It excludes the key, so key rotation does not invalidate a retry. A changed interpretation identity fences unfinished work as in D011. Already prepared/applied operations recover without another API request. This identifies application request semantics, not a provider's immutable model weights behind a mutable model ID.

## Explicit execution and verification

conversation-nebius requires an owner and inbox source; configuration alone performs no work. It emits sanitized worker status, not the saved food payload. Existing conversation-run remains synthetic. nebius-smoke sends one fixed synthetic food input and validates its expected action through the resolver without opening a database engine. It prints validation flags and the parser fingerprint on success. A smoke pass would establish one request/schema example, not language quality or production readiness.

Smoke follow-up on 2026-09-23: compare validated grams numerically with Decimal, so 100.0 and 100 represent the same expected quantity. A failed expectation reports schema-valid action kinds and backend resolution codes. Only known unresolved-field paths are printed; arbitrary paths become "other". No raw proposal or free text is exposed. These changes affect only the synthetic check, so the provider request and parser identity stay unchanged.

W004's required verification is offline protocol/CLI testing and PostgreSQL integration with injected responses, followed by independent review. The user has reported a live response that passed schema/reference validation but failed the expected-action check; the work brief owns this evidence and its limits. No successful expected-action result, final model selection, latency, cost, or broader Russian evaluation is claimed. Q09/Q10 retain those dependent choices and real-data lifecycle requirements. No removed evaluation corpus is recreated.

## Sources and related artifacts

### Request-format correction — 2026-09-23

After the user resolved key entry, their smoke command returned HTTP 422. Nebius's published OpenAPI version 20260916-b712a99a4 defines JsonSchemaResponseFormat with required name and schema fields. The old direct-schema payload lacks both and fails validation against that definition. The guide's Python example still shows the old shape, while its named-schema example and the API reference show the wrapper. Prefer the machine-readable API contract for the request envelope.

Send response_format as {"type":"json_schema","json_schema":{"name":"nutrition_parser_output","schema":ParserOutput.model_json_schema(),"strict":true}}. Preserve all inner schema constraints and local validation. Adapter identity becomes nebius-chat-v3 and hashes the actual wrapper, including name, strictness and schema. This intentionally changes interpretation identity for unfinished work; frozen prepared commands still resume under W003's existing rules. No migration, provider fallback or error-body logging is added.

The [API reference](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion) and [OpenAPI document](https://api.tokenfactory.nebius.com/openapi.json) were fetched on 2026-09-23. An attributed extraction of the two response-format definitions is retained in [nebius-response-format-openapi.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/fixtures/nebius-response-format-openapi.json?type=file&root=%252F), with API version and full-source hash. Tests validate the outgoing format against this independent provider contract. This fixes a proven request-shape mismatch; a successful live response with the selected model and full inner schema still needs verification.

Official sources fetched on 2026-09-22: [Nebius quickstart](https://docs.tokenfactory.nebius.com/quickstart) for origin/authentication, [structured output](https://docs.tokenfactory.nebius.com/ai-models-inference/json) for JSON Schema format/model-dependent support, and [text generation](https://docs.tokenfactory.nebius.com/api-reference/examples/text-generation) for completion fields. The guide examples include formatting inconsistencies; local tests verify our intended payload, while the actual schema/model combination still requires live confirmation.

Scope and acceptance belong to [004-nebius-adapter.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F). D012 extends D009/D011's selected provider and worker boundary without changing product scope or portable contracts.
