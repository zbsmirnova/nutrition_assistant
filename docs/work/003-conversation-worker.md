# W003 — Turn a clear food message into a durable command

Status: done.
Milestone: M2 (second slice; does not complete M2).
Owner: lead assistant, architect/developer; independent review completed by independent_m1_qa.
Updated: 2026-09-22.

## Outcome and scope

Connect the durable Telegram inbox to the existing food service through a parser interface and backend resolver. For one explicit consumption statement, such as “Съела 100 г творога 5% «Марка А»”, use an unambiguous owned synthetic product and compatible quantity to save one entry and queue the existing Russian entry-plus-day acknowledgment. The product's nutrition comes from its pinned catalog version, never from model arithmetic. Under D010, generic “100 г творога” remains unresolved when the fat percentage/product variant is unknown.

This slice implements the worker and resolution boundary using controlled parser responses. It does not establish that a live model understands Russian messages. The user selected Nebius Token Factory cloud inference and will supply its key as a secret (D009). A separate Nebius adapter and measured evaluation follow; the exact model and Q10's remaining data-lifecycle choices are still open. Worker development does not require the key.

Initial executable scope is one independent product-food addition with explicit quantity, known unit/basis, and a deterministically resolvable source date. Preserve M1's operation identity for position zero. Persist and expose non-logging, unsupported, unresolved, and failed dispositions so an input cannot disappear or be mistaken for a successful food save. Do not attempt an arbitrary first action from a multi-action proposal.

Clarification replies, mixed-message partial saving, corrections/delete/undo, recipe sources, catalog editing, conversational references, and check-ins follow in later slices. Those accepted v1 requirements remain necessary to finish M2 and the release. In W003, missing facts and unsupported actions remain durable deferred work without guessed food or a success acknowledgment. This worker is a development boundary, not a complete personal bot.

## Requirements and decisions

FOOD-001, FOOD-002, FOOD-005, FOOD-006, CALC-001/CALC-002, and DATA-001–DATA-003 govern this slice. Reuse D002's frozen commands and atomic execution, D003's scoped relational storage, D006's arithmetic, and D007's inbox/outbox transport.

D010 refines FOOD-002 for dairy product identity. The resolver must recognize missing/conflicting fat percentage as material even if the user's catalog has only one dairy candidate. An exact identified product/profile or an explicit matching percentage can resolve that detail without another question. The full question/answer flow remains subsequent clarification work.

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
| W003-A11 | An unspecified material dairy fat percentage or conflict with a candidate yields durable unresolved work and no food mutation, even with only one catalog candidate. An explicitly identified matching product/profile passes without a redundant fat question. A percentage alone never becomes eaten grams or a complete invented nutrition profile. |

## Implementation checklist

- [x] Define the next bounded slice and identify the existing service/contract constraints.
- [x] Record the worker state/recovery decision, including claims, retries, frozen interpretation, deferred input handling, and upgrade behavior.
- [x] Add durable worker state and migration; preserve existing operation identities and source ownership.
- [x] Implement the provider-neutral interface and controlled synthetic adapter.
- [x] Build scoped product context and the supported single-food/date resolver.
- [x] Connect prepared-command recovery and the existing food service/outbox; add an explicit synthetic worker command.
- [x] Add requirements-based intent, isolation, date, crash/concurrency, and populated-migration checks.
- [x] Run relevant regressions, maintain setup/specifications, and provide a reproducible review handoff.
- [x] Obtain independent review and address findings; close out under the authorized completed-slice commit workflow.

## Developer handoff

Preparation baseline: commit 4b5120be5ca5423c24d64af91048da8793f795ea, the completed W002 transport slice. The repository currently has 106 passing checks recorded for that baseline. They do not cover W003 and were not rerun merely to write this brief.

W003 now implements migration 0004, the controlled parser boundary, scoped single-food resolver, durable worker, deferred-food counts, and synthetic CLI flow. D011 records its recovery and catalog identity rules. Developer verification contains 65 unit/protocol/resolver checks, 53 PostgreSQL integration checks, and 27 retained independent probes from M1/W002/W003. The developer report and independent review preserve source-specific runs and attribution.

Setup/run commands are in README. Limitations: no live Nebius or Telegram calls, no clarification question/answer handler, no multi-action execution, no general Russian parser, g/ml only, and bounded classified catalogs. Deferred unknown-date/context-dependent work cannot yet be assigned reliable daily pending counts. Prior review evidence applies only to its earlier snapshots.

## QA result and completion

Independent W003 review passed all eleven criteria for source 857b4097fc7f85b843bdc08169b5d61b9ecffa49f11fc98a554552252873d633. All five original defect groups, including the quantity-bound follow-up, are resolved. Final verification: 67 offline checks, 53 PostgreSQL integration checks, and 27 retained QA checks. The frozen source includes two separately authored corpus-integrity checks; those do not establish model accuracy. The separate corpus removal commit 4cd68b3 leaves 65 offline checks in the final project, with W003 runtime and tests unchanged.

Developer evidence: [003-conversation-worker-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/003-conversation-worker-developer.md?type=file&root=%252F). Independent verdict and retained failures: [003-conversation-worker-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/003-conversation-worker-qa.md?type=file&root=%252F). The closeout manifest separates unchanged reviewed runtime from subsequent documentation/evidence packaging.

W003 is complete for its synthetic single-food scope. M2 remains in progress; live Nebius interpretation, interactive clarification, mixed actions, and corrections require subsequent slices.
