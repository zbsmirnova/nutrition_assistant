# W002 — Durable private Telegram transport

Status: done.
Milestone: M2 (first slice; does not complete M2).
Owner: lead assistant, architect/developer; independent QA: independent_m1_qa.
Updated: 2026-09-22.

## Outcome and scope

Connect the existing food service to a private Telegram transport boundary. Long polling resolves the sender through an explicitly provisioned account, persists supported text before advancing the durable cursor, and preserves reply/date evidence. A bot-scoped sender renders committed food outcomes in Russian. Exercise the full boundary with synthetic Telegram responses and real local PostgreSQL.

This slice supplies transport, not a natural-language parser. Received text alone never creates food. A later resolver supplies validated commands through the existing service. Provider/data-sharing decisions Q09/Q10 remain open; no actual user messages or external sends are used in implementation checks. Live operation requires an explicitly configured bot and account mapping. Public onboarding, groups, media, message edits, clarification/correction handlers, and deployment are outside this slice.

## Requirements and decisions

FOOD-001, FOOD-006, CALC-001/CALC-002, DATA-001–DATA-003, UX-001. D007 records local long polling, account mapping, durable cursor behavior, and delivery classification. Reuse the existing command/outcome contracts. Do not reinterpret source dates or manufacture nutrition from transport text.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W002-A01 | Only an explicitly linked private human sender/chat for the verified bot is accepted. Other accounts/groups/bots and unsupported update types cause no personal or food writes. |
| W002-A02 | Text, source instant/timezone, reply-to message ID, and forwarding flag survive ingestion. Text containing a claimed user ID cannot select the application owner. |
| W002-A03 | Polling advances its durable cursor only after accepted messages commit. A failure before checkpoint or concurrent poller cannot lose or duplicate a source. Recovery reuses the same inbox record. |
| W002-A04 | Existing M1 inbox hashes and results remain replayable after upgrade. Migration head and metadata match; populated migration preserves prior food/outbox data. |
| W002-A05 | A sender claims only its configured bot's committed responses. Successful real-adapter responses retain Telegram's message ID; no send occurs inside the domain transaction. |
| W002-A06 | Russian replies contain saved-entry nutrition and date-labelled day totals. Unknown, partial, and zero remain distinct; untrusted food descriptions cannot add formatting/link previews or overflow the message limit. |
| W002-A07 | Explicit rejection becomes failed; a confirmed rate limit waits at least retry_after with bounded attempts; ambiguous network/API outcomes become uncertain without automatic resend. Tokens, payloads, and API descriptions do not appear in operational errors. |
| W002-A08 | The client verifies bot identity and refuses an active webhook without deleting it or dropping updates. CLI setup/commands and implementation limits are documented. Tests make no live Telegram calls. |

## Implementation checklist

- [x] Record transport decision and create minimal migration.
- [x] Implement authenticated normalization, private account provisioning, cursor recovery, and single-poller coordination.
- [x] Implement bot-scoped response delivery and Russian rendering.
- [x] Add independent expected-value, transport, and PostgreSQL recovery/isolation checks.
- [x] Run regression suites and maintain setup/specifications/roadmap.
- [x] Provide a reproducible QA handoff, address findings, and record the verdict.

## Developer handoff

Implementation and independent review are complete for the transport scope. Setup and explicit transport commands are in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F). Migration head is 0003. Protocol checks run without network access; integration checks use disposable local PostgreSQL schemas. A prepared fixture command stands in for the future resolver in the synthetic end-to-end transport check. Live parser/provider and real-data use remain separate work. Tokens must be configured locally through the environment, never supplied in chat or committed.

Exact source identities, commands, results, and limits are recorded in [002-telegram-transport-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-developer.md?type=file&root=%252F) and [002-source-manifest.json](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-source-manifest.json?type=file&root=%252F). Review found a malformed chat-ID receipt case; strict receipt validation and independent recheck resolved W002-QA-D01.

## QA result and completion

Independent QA passed all eight criteria on attempt 2, source 4ba4769b0cddba32ece9d2b001011ce51ef7614c694d5964c19c22b1c30f2ba2. Evidence and execution attribution are in [002-telegram-transport-qa.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/002-telegram-transport-qa.md?type=file&root=%252F). QA independently reviewed requirements/code and ran protocol checks; the lead executed database checks at QA's request and QA assessed the raw outputs. No unresolved substantive finding remains.

The repository now has 52 contract/arithmetic/protocol tests, 38 integration tests, and 16 retained QA checks. The six new QA checks passed from their retained location after packaging. Earlier database evidence was inherited for the unchanged database paths across the one-line receipt fix; the report records targeted rechecks explicitly. Status/evidence edits and retained probes are post-review additions; production code remains identical to attempt 2.

W002 is complete; M2 remains in progress. Synthetic transport verification is not a live Telegram, parser, or production-release verdict.
