# D012 — Explicit Nebius requests and durable provider failure handling

Kind: technical.
Status: accepted for W004 under delegated implementation authority.
Recorded: 2026-09-22.
Decision owner: lead architect/developer.
Authority: the user selected Nebius in D009 and instructed continuing with its adapter after W003.

## Decision

Use the standard-library HTTPS client against the fixed api.tokenfactory.nebius.com origin and /v1/chat/completions path. Send bearer authentication from NEBIUS_API_KEY, require an explicit NUTRITION_LLM_MODEL, and retain certificate verification. No configurable alternate host, redirect following, SDK retry loop, or provider fallback is introduced. No dependencies or migration change.

Request one non-streaming completion with temperature 0 and max_tokens 4096. Use response_format.type=json_schema with the existing ParserOutput-generated schema directly in json_schema, as shown by Nebius's structured-output guide. Include the schema in the system prompt as well. This preserves the actual contract; there is no schema simplification, JSON repair, or fallback to arbitrary JSON. Exact chosen-model compatibility remains a live verification task.

The request contains only the source text, source-local date and time zone, and W003's public product candidate fields with scoped tokens. Explicitly project candidate fields again at the adapter boundary. Names and source text are data in a separate user message; the system prompt instructs faithful intent extraction and no invented consumption, identities, quantities or nutrients. These instructions do not establish resistance to every prompt injection or model accuracy; existing local validation/resolution remains mandatory.

Set a 30-second socket timeout and a 256-KiB request/response limit. The timeout is a socket inactivity bound, not a guaranteed end-to-end deadline; W003's database lease fences late results. The adapter closes every connection and never reads an error body. Slow responses can expire a worker lease; operator resumption may repeat an uncommitted inference, so provider billing is not exactly once.

Accept only one index-zero assistant choice ending with stop, nonempty content, no refusal, and no tool/function call. Validate the content against ParserOutput and scoped evidence/references before returning it to W003, which validates/resolves again. Reject malformed envelopes, truncated/refused outputs, invalid JSON/schema/evidence, oversized responses and permanent non-200 statuses. Operational error strings contain no key, model payload, source text, provider body or exception details.

Transient network errors, HTTP 408/429 and 5xx use the existing durable worker retry budget of three claims. Retry-After supports integer seconds or HTTP dates after normalizing surrounding HTTP spaces/tabs; the stored delay is the greater of the hint and existing exponential backoff. A 429 without a usable hint waits at least 60 seconds. Hints beyond one day stop visibly instead of retrying earlier than instructed. Permanent provider rejection becomes a terminal failed job; no food/outbox mutation occurs. The inbox remains inspectable. Resetting terminal jobs after operator corrections remains later explicit recovery tooling, not silent automatic reprocessing.

The parser version hashes adapter policy, fixed endpoint, timeout/limits, model, system prompt, schema and generation parameters. It excludes the key, so key rotation does not invalidate a retry. A changed interpretation identity fences unfinished work as in D011. Already prepared/applied operations recover without another API request. This identifies application request semantics, not a provider's immutable model weights behind a mutable model ID.

## Explicit execution and verification

conversation-nebius requires an owner and inbox source; configuration alone performs no work. It emits sanitized worker status, not the saved food payload. Existing conversation-run remains synthetic. nebius-smoke sends one fixed synthetic food input and validates its expected action through the resolver without opening a database engine. It prints only validation flags and the parser fingerprint. A smoke pass would establish one request/schema example, not language quality or production readiness.

W004's required verification is offline protocol/CLI testing and PostgreSQL integration with injected responses, followed by independent review. A live smoke run needs a configured key/model; no live result, chosen model, latency, cost, or broader Russian evaluation is claimed. Q09/Q10 retain those dependent choices and real-data lifecycle requirements. No removed evaluation corpus is recreated.

## Sources and related artifacts

Official sources fetched on 2026-09-22: [Nebius quickstart](https://docs.tokenfactory.nebius.com/quickstart) for origin/authentication, [structured output](https://docs.tokenfactory.nebius.com/ai-models-inference/json) for JSON Schema format/model-dependent support, and [text generation](https://docs.tokenfactory.nebius.com/api-reference/examples/text-generation) for completion fields. The guide examples include formatting inconsistencies; local tests verify our intended payload, while the actual schema/model combination still requires live confirmation.

Scope and acceptance belong to [004-nebius-adapter.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F). D012 extends D009/D011's selected provider and worker boundary without changing product scope or portable contracts.
