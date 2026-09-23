# Contributor and agent instructions

## Responsibility and reading order

The user has assigned documentation maintenance to the lead assistant. Keep the project documents current as part of each relevant task; do not wait for a separate reminder. This responsibility applies during active project work and handoffs, not as a claim of unattended background monitoring.

Start with [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F) and the current work brief linked from [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F). Read the relevant architecture/specification and decision records before changing that behavior. Use [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F) for validation and [development-process.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/development-process.md?type=file&root=%252F) for artifact ownership.

Explicit user decisions govern the project. Reflect them in the documents. When code, contracts, or prose disagree, identify the conflict and resolve it within the authorized task; do not silently promote a proposal to an accepted requirement. Continue independent work when a product question is unresolved. Ask only when the answer is needed for the dependent behavior.

## Current implementation boundary

The executable implementation includes M1 persistence, W002 private Telegram transport, and W003's provider-neutral conversation worker with a controlled synthetic parser and bounded single-food resolver. Job state and product identity metadata use migration 0004. Independent completion/review status belongs in the work brief. No live bot/model integration is claimed. W004 adds the Nebius adapter and explicit worker/synthetic-smoke commands, with protocol checks using injected responses. Live compatibility/model quality, conversational clarification/corrections, recipes, observations, and scheduling remain future work. Keep protocol, database, live-transport, and live-model evidence distinct.

The existing deployment files describe Open WebUI, not the new nutrition backend. The first implementation brief covers local synthetic-data development. Deployment and real-data provider use have unresolved requirements recorded in the decision register.

## Document maintenance rules

Update only the documents affected by a change, in the same working change as the implementation or accepted decision:

| Change | Update |
| --- | --- |
| Product behavior, scope, enduring rule | Constitution, relevant specification, consequential decision record, affected task/QA criteria. |
| Significant technical choice | Decision record and index; architecture/data model if affected. Record status and decision authority truthfully. |
| Milestone progress or dependency | Roadmap. Do not call a milestone complete solely because contract shapes exist. |
| Task progress, scope, or handoff | Its work brief; task status has one home. |
| Contract model change | Python models, generated schemas, affected examples/tests, typed-contract guide. |
| Setup, runnable commands, dependencies | README and relevant validation instructions. |
| QA execution | Report exact revision, evidence, coverage limits, defects, and verdict; link it from the task. |
| Newly resolved question | Update the single question register and the resulting authoritative specification/decision. |

Do not duplicate the backlog, decision narrative, or acceptance criteria across files. Keep historical decisions and QA evidence; add a superseding decision or a new verification attempt when needed. Never invent an acceptance date, a test run, a reviewer, or a pass.

## Implementation conventions

- Keep model interpretation separate from backend authorization, arithmetic, and writes.
- Preserve stable entry identities, scoped references, pinned nutrition versions, explicit unknowns, and per-day observation uniqueness.
- Use synthetic examples during development. Do not place credentials or real personal messages in fixtures, commits, ordinary logs, or QA reports.
- Reuse the existing contract types. Python models are the schema source; do not edit generated JSON Schemas by hand.
- Keep migrations, calculations, and transactional failure behavior reviewable. Do not claim an outbox ensures exactly-once visible Telegram delivery.
- Inspect repository state first and preserve unrelated user changes. The user has authorized a focused local commit after each completed, tested slice, including its maintained documentation and QA evidence. Continue this practice without asking again. Do not include unrelated or unfinished work, push, deploy, or rewrite existing commits without the corresponding authorization. Review snapshots may still identify work before its completion commit.
- Roles are architect, developer, and QA; they need not run concurrently. Do not spawn additional agents without applicable authorization. If parallel work is authorized, use isolated branches/worktrees and explicit file ownership.

## Verified checks

From the repository root, install the pinned runtime dependencies and start local PostgreSQL as documented in [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F), then:

~~~sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/integration -v
.venv/bin/python -m unittest discover -s tests/qa -v
git diff --check
~~~

When a contract model changes, regenerate schemas before those checks:

~~~sh
.venv/bin/python -m nutrition_contracts.export
~~~

The existing suite checks generated-schema drift. For documentation-only changes, inspect links, document ownership/status consistency, and formatting; do not add implementation-mirroring tests or claim independent QA occurred.

The explicit integration and retained QA suites require local PostgreSQL and create/remove only their own random schemas. They fail when the database is unavailable. Default test discovery runs offline contract, arithmetic, protocol, and resolver checks. User-run synthetic Nebius smoke attempts have returned HTTP 401 and then 422; no successful live interpretation is verified. The adapter's response-format wrapper is now checked against an attributed provider OpenAPI fixture. Real Telegram checks remain unverified. A changed contract requires regeneration; a changed migration/transaction requires both PostgreSQL suites.

## Completion and handoff

Before reporting completion, check the task criteria, relevant tests, documentation changes, and unresolved limitations. Provide the exact reviewable revision or explicitly identified working-tree snapshot and instructions to reproduce it. A QA review of uncommitted changes is not a review of the base commit alone.

Keep developer verification separate from independent QA. If no independent QA ran, say so. Mark a work brief done only when its definition of done is met, and update milestone status only when the milestone's own exit criteria are met.
