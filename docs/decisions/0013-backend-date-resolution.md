# D013 — Backend-owned date resolution

Kind: technical.
Status: accepted for M2 under delegated implementation authority.
Recorded: 2026-09-23.
Decision owner: lead architect/developer.
Authority: architecture discussion following the Nebius smoke result; consistent with CALC-001 and the typed contract.

## Decision

The model extracts date evidence when the user explicitly writes a date phrase. The backend owns the effective date. It uses the source message's local date when the source contains no date evidence, resolves supported explicit and relative phrases using the original message date and user time zone, and defers unsupported or ambiguous date evidence.

The model may not move a food entry to a different date by returning a date that is absent from the source. This protects the record from model defaults such as adding `сегодня` to an undated message. The backend's date library and source timestamp are authoritative; execution time and model-generated calendar dates are not.

Because this changes the interpretation of an existing source and hint combination, the resolver version advances from `single-food-resolver-v3` to `single-food-resolver-v4`. Unfinished interpretation contexts carrying the previous version are fenced by the conversation worker and must be interpreted again. Prepared or applied commands retain their stored command and remain recoverable without another model call.

Examples:

- `Съела 100 г творога` uses the source message's local date.
- `Вчера съела 100 г творога` extracts `вчера`; the backend resolves the previous local date.
- `Съела 100 г творога 20 сентября` extracts the exact phrase; the backend parses it according to supported date rules.
- An unsupported or conflicting phrase remains unresolved and does not enter totals.

## Consequences

The portable parser contract retains `date_hint` for evidence and clarification, but date arithmetic and authority stay outside the model. A model hint on an undated source is ignored rather than allowed to cause an artificial date or a needless clarification. This remains separate from the model's general intent and food-identity responsibilities.

The backend resolver has focused tests for absent, explicit, relative, conflicting and model-invented date hints. No migration or provider-specific request change is needed.

Related: [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), D011 and D012.
