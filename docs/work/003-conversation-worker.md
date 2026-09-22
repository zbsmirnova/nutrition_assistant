# W003 — Turn a clear food message into a durable command

Status: ready.
Milestone: M2 (second slice; does not complete M2).
Owner: lead assistant, architect/developer; independent reviewer not yet assigned.
Updated: 2026-09-22.

## Outcome and scope

Connect the durable Telegram inbox to the existing food service through a parser interface and backend resolver. For one explicit consumption statement, such as “Съела 100 г творога”, use an unambiguous owned product and compatible quantity to save one entry and queue the existing Russian entry-plus-day acknowledgment. The product's nutrition comes from its pinned catalog version, never from model arithmetic.

This slice implements the worker and resolution boundary using controlled parser responses. It does not establish that a live model understands Russian messages. The user selected Nebius Token Factory cloud inference and will supply its key as a secret (D009). A separate Nebius adapter and measured evaluation follow; the exact model and Q10's remaining data-lifecycle choices are still open. Worker development does not require the key.

Initial executable scope is one independent product-food addition with explicit quantity, known unit/basis, and a deterministically resolvable source date. Preserve M1's operation identity for position zero. Persist and expose non-logging, unsupported, unresolved, and failed dispositions so an input cannot disappear or be mistaken for a successful food save. Do not attempt an arbitrary first action from a multi-action proposal.

Clarification replies, mixed-message partial saving, corrections/delete/undo, recipe sources, catalog editing, conversational references, and check-ins follow in later slices. Those accepted v1 requirements remain necessary to finish M2 and the release. In W003, missing facts and unsupported actions remain durable deferred work without guessed food or a success acknowledgment. This worker is a development boundary, not a complete personal bot.

## Requirements and decisions

FOOD-001, FOOD-002, FOOD-005, FOOD-006, CALC-001/CALC-002, and DATA-001–DATA-003 govern this slice. Reuse D002's frozen commands and atomic execution, D003's scoped relational storage, D006's arithmetic, and D007's inbox/outbox transport.

The existing ParserOutput type and validate_parser_context function own proposal validation; CommandEnvelope owns the trusted command boundary. Read the conversation and typed-contract specifications before implementation. Do not invent a second parser schema or let a provider choose the actor, operation ID, database identity, or nutrition totals.

Q09's provider choice is resolved by D009; do not ask cloud versus local again. The intended secret variable is NEBIUS_API_KEY, with a separate NUTRITION_LLM_MODEL setting for the exact model ID. The non-secret configuration template and provider decision are prepared; no runtime adapter is implemented. Synthetic worker implementation can proceed independently. The single question register retains the remaining model/evaluation and Q10 data-lifecycle choices for their dependent work.

Q04's broader conversational ambiguity choices remain open. This slice can use the stored message timestamp and captured IANA time zone for no-date/today/yesterday and explicit ISO-date cases, retaining unsupported date expressions for later resolution. Processing after midnight must not silently change the target date. Reply-dependent and forwarded inputs must not be interpreted as standalone consumption without the later context-resolution rules.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W003-A01 | A controlled valid interpretation of one explicit food statement produces one entry with the independently expected nutrition, original local date, and one committed food-response intent. The synthetic transport flow can deliver its entry-plus-day acknowledgment. |
| W003-A02 | Candidate context is constructed from the authenticated owner's catalog. Unknown, wrong-kind, ambiguous, or foreign references cannot produce food. Resolve and pin a specific immutable product version; backend authorization is rechecked at execution. |
| W003-A03 | Reject malformed or out-of-context parser responses before any food mutation. Supplied quantity, units, date, and source basis must resolve without inventing facts or converting incompatible measurements. Unknown nutrients retain their existing coverage semantics. |
| W003-A04 | Controlled plan, question, product-definition, correction, ambiguous-food, and multi-action responses do not become a consumption addition. Their recorded dispositions distinguish intentional non-logging from deferred unsupported/unresolved work. No response falsely says food was saved. |
| W003-A05 | Retry or restart before/after interpretation persistence, command preparation, domain commit, and worker completion neither loses an accepted input nor duplicates food/outbox records. Resume a frozen interpretation/command rather than obtaining new identities after partial progress. Distinct new messages with identical text remain distinct inputs. |
| W003-A06 | Competing workers cannot apply contradictory interpretations for the same input. A stale worker cannot overwrite a newer claim or frozen result. Parser calls occur outside database transactions; bounded retries and terminal/deferred states prevent a failing input from blocking unrelated work. |
| W003-A07 | Source-date resolution survives midnight, daylight-saving transitions, and delayed processing. Unsupported or contradictory date hints remain unresolved. Reply-dependent and forwarded inputs cannot bypass context requirements. |
| W003-A08 | Upgrade from populated migration 0003 preserves inbox, prepared operations, food, and delivery state. Existing prepared/applied inputs resume without another parse or another addition. New worker state preserves owner-scoped constraints. |
| W003-A09 | Operator commands expose/resume worker progress with synthetic fixtures and no provider credentials. Operational errors omit personal message text, model payloads, and secrets. Record interpretation/schema/context versions needed to reproduce the synthetic check. |
| W003-A10 | Developer evidence and an independent review identify the exact tested source. Distinguish controlled-proposal checks from live-model accuracy and real Telegram checks, which remain not run in this slice. |

## Implementation checklist

- [x] Define the next bounded slice and identify the existing service/contract constraints.
- [ ] Record the worker state/recovery decision, including claims, retries, frozen interpretation, deferred input handling, and upgrade behavior.
- [ ] Add durable worker state and migration; preserve existing operation identities and source ownership.
- [ ] Implement the provider-neutral interface and controlled synthetic adapter.
- [ ] Build scoped product context and the supported single-food/date resolver.
- [ ] Connect prepared-command recovery and the existing food service/outbox; add an explicit synthetic worker command.
- [ ] Add requirements-based intent, isolation, date, crash/concurrency, and populated-migration checks.
- [ ] Run relevant regressions, maintain setup/specifications, and provide a reproducible review handoff.
- [ ] Obtain independent review, address findings, and commit the completed, tested implementation.

## Developer handoff

Preparation baseline: commit 4b5120be5ca5423c24d64af91048da8793f795ea, the completed W002 transport slice. The repository currently has 106 passing checks recorded for that baseline. They do not cover W003 and were not rerun merely to write this brief.

No W003 runtime changes, migration, parser call, or worker verification have run. Implementation must provide the exact reviewable revision/snapshot, migration and CLI instructions, executed checks, and remaining limitations here or in a linked developer report. Retain independent QA attribution; a developer test pass is not an independent verdict.

## QA result and completion

Not run. No W003 QA report exists yet. The implementation is done only when its scoped criteria have evidence, relevant regression suites pass, substantive defects are resolved, independent review is recorded, and affected documents are current. Completing this planning document does not complete the implementation or M2.
