# D009 — Nebius Token Factory for cloud interpretation

Kind: technical.
Status: accepted for provider selection and secret delivery.
Recorded: 2026-09-22.
Decision owner: product owner for the provider; architect for the integration boundary.
Acceptance evidence: the user stated, “the model will be cloud, from Nebius token factory, I'll provide a key as a secret”.
Related questions: Q09 (provider resolved; model and evaluation remain open), Q10 (retention and other data-lifecycle choices remain open).

## Context

W003 connects stored food messages to validated food commands. The provider choice is needed for the subsequent live adapter and Russian-language evaluation. CALC-001 keeps interpretation separate from authorization, reference resolution, arithmetic, and database writes.

## Decision

- Use Nebius Token Factory cloud inference. Do not reopen the cloud/local choice or substitute another provider without a new decision.
- The user supplies the API key through a secret, exposed to the application process as NEBIUS_API_KEY. Never ask for the value in chat or put it in a tracked file, command argument, log, or QA evidence. The assistant does not need to inspect or display the key.
- Use the documented HTTPS base URL https://api.tokenfactory.nebius.com/v1/ and chat-completions endpoint. The future adapter must use certificate verification, bounded timeouts, and sanitized errors; it must not forward credentials on redirects or fall back to another provider.
- Keep the exact model ID configurable as NUTRITION_LLM_MODEL. No model has been selected or evaluated yet; require an explicit model for live execution rather than copying a potentially outdated model from documentation examples.
- Use the existing ParserOutput contract and backend context validator. Nebius documents JSON Schema output, with model-dependent support. Verify the chosen model with this application's actual schema; do not equate provider JSON-mode support with tested intent accuracy or application validity.
- The provider request should contain the current message and bounded relevant product/context information needed for interpretation. Application user IDs, Telegram identities, unrelated observations, and full chat history are unnecessary for the initial single-message worker. Record the implemented request shape when building the adapter.
- Supplying a secret configures credentials; it must not automatically trigger inference, inbox processing, or deployment. Start live verification with explicit synthetic requests once the adapter, model setting, and key are available.

Provider selection authorizes designing and connecting Nebius for the requested interpretation purpose. It does not decide local raw-message/revision/backup retention, export/deletion, or secondary analytics. Keep those Q10 choices separate rather than asking the cloud/provider question again.

## Alternatives and consequences

A local model and other cloud providers were alternatives. The user's explicit selection resolves that tradeoff. The worker remains independent of provider transport so recovery and authorization can be tested with controlled proposals before a secret is supplied.

The key is not needed for local worker development or synthetic checks. The live model, request/schema compatibility, latency/cost, and evaluation results remain unverified. This decision does not claim an implemented adapter or a successful API call.

## References and replacement history

Official Nebius documentation checked on 2026-09-22:

- [Quickstart](https://docs.tokenfactory.nebius.com/quickstart): base URL, bearer authentication, and NEBIUS_API_KEY environment variable.
- [Structured output and JSON](https://docs.tokenfactory.nebius.com/ai-models-inference/json): JSON Schema response format and model-dependent support.
- [Text generation](https://docs.tokenfactory.nebius.com/api-reference/examples/text-generation): chat-completions request fields.

At this decision's initial recording, the adapter was future work; these sources established its intended integration contract, not live verification. This resolved the provider portion of Q09 without superseding D002–D007's execution, storage, calculation, or transport rules.

Implementation follow-up: D012 and [004-nebius-adapter.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/004-nebius-adapter.md?type=file&root=%252F) record the adapter added after this decision. Its offline checks do not establish live compatibility.
