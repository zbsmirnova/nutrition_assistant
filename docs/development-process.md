# Development process and document ownership

Status: adopted on 2026-09-22 at the user's request.
Maintenance owner: lead assistant.
Decision record: [0005-document-maintenance.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0005-document-maintenance.md?type=file&root=%252F).

The user should not need to remind the assistant to maintain project documentation. During each relevant task, update the affected requirements, decisions, specifications, progress, and verification instructions as part of the work. Keep changes in the same repository so behavior and its documentation can be reviewed together.

## Where information belongs

| Artifact | Owns | Does not own |
| --- | --- | --- |
| [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/README.md?type=file&root=%252F) | Entry point, verified setup commands, short dated implementation summary, navigation. | A second backlog or complete specification. |
| [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F) | Product idea, goals, scope, non-goals, stable requirement IDs. | Detailed tables, delivery mechanics, or speculative metrics. |
| [AGENTS.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/AGENTS.md?type=file&root=%252F) | Agent reading order, working conventions, checks, maintenance and handoff instructions. | A copy of product requirements. |
| [architecture-plan.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/architecture-plan.md?type=file&root=%252F) | System boundaries, data flow, trust, reliability, operations. | Milestone status or the open-question register. |
| [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F) | Detailed logical schema, relationships, ownership, constraints. | A claim that migrations have run. |
| [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F) | User-visible interpretation and interaction rules, with proposed defaults identified. | Implementation task status. |
| [typed-contracts-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/typed-contracts-v1.md?type=file&root=%252F) | Executable contract guide, schema source, examples, validation limits. | Proof of live-model or persistence behavior. |
| [README.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/README.md?type=file&root=%252F) and numbered records | Decision index, status, authority, rationale/history, single open-question register. | Duplicated current specifications. |
| [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F) | Milestone sequence, dependencies, exit criteria, milestone progress. | Every task checkbox. |
| [001-persist-food-entry.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/001-persist-food-entry.md?type=file&root=%252F) and subsequent briefs | A slice's scope, acceptance criteria, task status, implementation checklist, developer handoff. | A separate copy of roadmap status. |
| [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F) | Verification layers, evidence rules, definition of done. | A blanket declaration that the application passed. |
| [scenarios-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/scenarios-v1.md?type=file&root=%252F) | Preserved behavioral scenario inventory and links to executable coverage as it is added. | Detailed duplicate scripts or execution results. |
| QA reports created from [TEMPLATE.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/TEMPLATE.md?type=file&root=%252F) | Exact reviewed revision, checks/evidence, defects, limitations, verdict. | Unverified results or a verdict for later revisions. |

Python models are the source for portable JSON Schemas. Regenerate schemas from those models and check drift when models change. Executable tests and evaluation datasets own runnable scenarios; prose identifies the required behavior and points to coverage.

## Working loop

1. **Define the slice.** Write or refine one brief with a concrete outcome, boundaries, observable acceptance criteria, and necessary decisions.
2. **Resolve necessary choices.** Record consequential decisions and distinguish accepted requirements from proposals. The architect can settle routine technical choices within delegated scope; unresolved product tradeoffs go to the product owner only when dependent work needs the answer.
3. **Implement and maintain.** Make the code change, update affected specifications/examples/commands, and maintain the brief. Continue independent work while a question is pending.
4. **Developer checks and handoff.** Run checks appropriate to the slice. Provide reproducible setup, revision, results, and known limitations in the same brief.
5. **Independent QA.** Derive checks from requirements, evaluate the stated revision, and record results and defects. Do not label developer self-checks as independent review.
6. **Fix and recheck.** Preserve previous evidence and associate new checks with the changed revision.
7. **Close and commit the slice.** Verify its definition of done, link actual QA evidence, update task/milestone status appropriately, and create a focused local Git commit containing the slice's code, documentation, and evidence. The user has authorized this as the ongoing workflow; do not ask again for each completed slice. Preserve unrelated changes and do not push or deploy without the corresponding authorization.

Documentation-only work needs document/link/status consistency checks; it does not require a simulated application QA report.

## Status and authority

Work-brief statuses: draft, ready, implementing, in QA, done, blocked.
Milestone statuses: planned, in progress, complete, blocked.
Decision statuses: proposed, accepted, rejected, superseded.

Use stable IDs for requirements, decisions, open questions, task acceptance criteria, and QA defects. Record who decided and the actual source of acceptance. “Recorded on” is distinct from the date of an earlier chat message. Implementation is not evidence that an unanswered product question was approved.

The constitution describes enduring accepted rules; detailed specifications refine them. If code, examples, decisions, and requirements disagree, identify and resolve the discrepancy rather than applying a simplistic newest-file-wins rule. Preserve historical reasoning while updating the current behavior.

## Responsibilities

| Role | Responsibility |
| --- | --- |
| Product owner | Product priorities, unresolved user behavior, consequential operating/data constraints. |
| Lead assistant / architect | Coherent requirements and design, decision status, task readiness, document maintenance, cross-document consistency. |
| Developer | Implementation, relevant checks, affected technical documentation, reproducible handoff. |
| QA | Independent expected outcomes, revision-specific verification, defects, coverage limits, rechecks. |

These are responsibilities, not a requirement to run several agents for every task. Parallel editing requires applicable authorization, isolated branches/worktrees, and explicit file ownership. QA can work sequentially from a concrete handoff. A reproducible working-tree snapshot can identify work awaiting review; commit the completed, tested slice afterward under the user's standing instruction. Do not expose unrelated changes or commit incomplete work merely to supply a revision number.

## Maintenance checkpoints

Before changing behavior, read the relevant accepted requirement and decision. During work, update documents affected by the change. Before declaring completion, check document links, status/authority labels, acceptance evidence, actual commands, and unresolved limitations.

For a new user decision: update the requirement/specification, resolve its question-register entry, record consequential rationale, and adjust affected criteria. Do not ask again about already accepted decisions. For a technical choice: record the chosen approach and delegated authority without falsely attributing it to the user.

Use the existing templates rather than inventing different formats per agent:

- Decision record: [TEMPLATE.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/TEMPLATE.md?type=file&root=%252F).
- Work brief / developer handoff: [TEMPLATE.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/TEMPLATE.md?type=file&root=%252F).
- QA execution report: [TEMPLATE.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/TEMPLATE.md?type=file&root=%252F).

Create reports when there is an actual revision and observed evidence. Leave “not run” visible until then. Keep sensitive personal data and secrets out of templates, examples, logs, and reports.

## Current adoption state

The constitution, contributor instructions, decision records/index, roadmap, QA strategy/scenario inventory, templates, and first implementation brief are established. The architecture overview now links to the dedicated roadmap and question register; detailed check-in rules live with the conversation specification.

Current milestone progress and the developer-verified baseline are maintained in [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F). The first brief owns its preparation and QA status. Report templates remain templates until actual verification occurs; they do not imply an independent review.
