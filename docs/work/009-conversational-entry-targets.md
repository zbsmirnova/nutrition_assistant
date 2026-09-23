# W009 — Resolve conversational food-entry targets

Status: done.
Milestone: M2.
Owner: lead assistant, architect/developer; developer verification complete.
Updated: 2026-09-23.

## Outcome and scope

Use backend-owned entry context to turn bounded parser proposals into W008 correction, delete, and undo commands. Reply-linked targets and unique entry candidates can mutate the intended entry; ambiguous descriptions and missing targets remain unresolved.

The slice supports one-component exact quantity corrections, delete, and undo of the prior active revision. It does not implement arbitrary natural-language target search, multi-component edits, pending corrections, message edits, date/meal disambiguation, or live-model quality.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W009-A01 | Parser context exposes opaque current-entry candidates and maps a reply to the committed entry operation without exposing database IDs to the parser. |
| W009-A02 | A reply-linked `correct_food` quantity proposal updates the same entry through W008 and does not create a new portion. |
| W009-A03 | An entry-candidate `delete_food` proposal removes the entry, and `undo_food` restores its prior active revision. |
| W009-A04 | A described target with multiple current matches remains unresolved and creates no prepared command. |
| W009-A05 | Forwarded/unmatched replies and unsupported multi-component changes do not mutate food. |
| W009-A06 | Existing add-food, clarification, correction persistence, provider, transport, migration, ownership, and QA checks remain green. |

## Implementation checklist

- [x] Add scoped entry context and reply-to-entry lookup to the conversation worker.
- [x] Resolve bounded correction/delete/undo proposals into guarded typed commands.
- [x] Add PostgreSQL coverage for reply correction, candidate delete/undo, ambiguity, and parser privacy.
- [x] Run offline, integration, and retained QA suites and record the exact revision.
- [x] Commit the completed slice with maintained documentation and QA evidence.

## Handoff

W008 provides the transactional command handlers and revision guards. The implementation is committed in `1bb79ebb5bb952d5007692999a4c772806dd9c8c`. Offline tests pass (`96`), PostgreSQL integration passes (`68`), and retained QA passes (`32`). No migration was needed. The next broader step is clarification of ambiguous targets and support for additional correction fields.

## QA result and completion

Developer verification passes for the bounded conversational-target workflow. Evidence is in [009-conversational-entry-targets-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/009-conversational-entry-targets-developer.md?type=file&root=%252F). No independent W009 review, live Nebius, or real Telegram behavior is claimed.
