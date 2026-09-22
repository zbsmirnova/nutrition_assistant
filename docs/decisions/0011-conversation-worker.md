# D011 — Frozen single-food interpretation and recoverable work

Kind: technical.
Status: accepted for W003 under delegated implementation authority.
Recorded: 2026-09-22.
Decision owner: lead architect/developer.
Acceptance evidence: the user instructed proceeding to the next implementation step after the W003 flow and D010 dairy rule were described. The locking, context, and migration details are delegated technical choices.
Related questions: Q04 (bounded standalone-message resolution only); Q09 remains the live Nebius adapter/evaluation work.

## Decision and implemented scope

Migration 0004 adds one owner-scoped conversation job per durable inbox source. Jobs distinguish processing, prepared/ready, retry, applied, non-logging, unresolved, unsupported, rejected, and failed outcomes. Inputs without jobs remain discoverable after a crash. No message is deduplicated by its text.

Use short user-row locks when claiming or changing a job. A random claim token and database-clock lease fence interpretation results; an expired or replaced worker cannot freeze a proposal. Parser calls occur outside transactions. A parser failure retries with bounded exponential delay, at most three claims without a frozen command; invalid proposals are rejected. Failed/unresolved/unsupported jobs remain inspectable and do not block unrelated inputs. Terminal dispositions are not silently reinterpreted on another run.

Freeze source text/local date/time zone, context revision, catalog candidates, schema/context/resolver versions, and parser version before the call. The parser sees bounded product context with opaque tokens, not database IDs or account/Telegram identity. The synthetic adapter binds its response to the exact input text, ordered candidate names, and fixture fingerprint. It does not use Nebius credentials or make network calls.

Validate the existing ParserOutput and scoped-context contract. In one short transaction, freeze the validated proposal and its disposition together with any prepared command. Reuse M1's position-zero operation identity and preparation helper; execution retains the atomic mutation/revision/result/outbox boundary. A crash after preparation resumes the stored command without parsing again. Existing M1 prepared/applied inputs also recover without a parser. Domain execution may be retried concurrently because the frozen command is immutable and its application is idempotent.

## Resolver boundary

W003 handles one independent product addition with explicit matching g/ml evidence, compatible as-supplied weight basis, a scoped product source, and a supported date. Today/yesterday/no-date resolve from the captured source instant and IANA time zone; an explicit ISO date is supported. Contradictory, missing, or unsupported date evidence remains unresolved. Unit conversions, reply-dependent/forwarded inputs, multi-action execution, estimates, and other domain commands remain deferred.

Versioned product identity adds food_kind (general/dairy, or unknown for legacy rows) and optional declared_fat_percent. The latter is a label identity attribute, not a replacement for nutrient columns. Legacy rows remain unclassified instead of inventing a category. Existing prepared commands still execute against their pinned versions. Catalog identity must be supplied explicitly when provisioning new synthetic products; a future catalog service must retain the same provenance/versioning rules.

For dairy, an explicit percentage must match the source identity. Missing percentage on a generic mention stays unresolved even if only one catalog candidate exists. A complete matching catalog name with a distinguishing non-dairy word can identify a saved product without repeating its percentage. Duplicate indistinguishable names remain ambiguous. Resolver v3 also requires the selected product’s distinguishing name/brand words to occur in the source, rejects quantity ranges, bound prefixes, and approximation markers, checks explicit raw/cooked evidence against the profile, and defers unsupported relative-date markers. Decimal quantity and percentage spans are excluded from date detection. Source evidence checks are deliberately conservative and are not a general Russian-language parser or a live-model accuracy guarantee.

An unresolved add-food proposal with a known target date contributes one pending-food count to the day, never nutrition. Unknown-date/context-dependent inputs and unsupported multi-action messages remain visible in operator job status; they cannot yet be assigned reliable per-day pending-action counts. Full clarification identities, replies/resumption, multi-item coverage, and corrections remain later M2 work. No clarification is sent by W003.

## Consequences and limits

The first catalog context is bounded to 64 current owned versions. If the catalog is larger, the job is explicitly unsupported rather than silently truncating candidates. Relevance retrieval belongs with later live-adapter work. Parser, resolver, or context-version changes cannot silently replace an unfinished interpretation; a mismatch becomes a visible failed job. Frozen work remains executable without the earlier adapter.

Operational status and parser failure reasons contain IDs/status codes, not message text, catalog payloads, or secrets. Raw source/context and accepted proposals remain local application state under the eventual Q10 retention policy. Rejected provider payloads and exception messages are not copied into operational output.

No changes to the portable parser/command/outcome schemas are required. The new synthetic CLI and tests do not constitute a live Nebius, real Telegram, or personal-release verification. The selected cloud provider and secret contract remain D009.

## References

- [003-conversation-worker.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/003-conversation-worker.md?type=file&root=%252F) owns acceptance and verification status.
- [conversation.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/conversation.py?type=file&root=%252F) owns durable orchestration.
- [interpretation.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/interpretation.py?type=file&root=%252F) owns the adapter boundary and scoped resolver.

D011 extends D002/D003 without replacing their operation identity, ownership, arithmetic, or outbox rules. D010 remains the accepted dairy behavior.
