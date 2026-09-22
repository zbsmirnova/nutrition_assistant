# D005 — Repository documentation and assistant maintenance

Kind: process.
Status: accepted.
Recorded: 2026-09-22.
Decision owner: product owner; execution owner: lead assistant.
Acceptance evidence: “create this docs and fill what needed for the current stage. This docs maintenance is your responcibility”.

## Decision

Adopt the proposed lightweight document structure in the repository: product constitution, contributor instructions, current architecture/specifications, decision index and records, roadmap, implementation work briefs, QA strategy, and QA report templates.

The lead assistant owns maintaining these artifacts as part of each relevant task. Update affected requirements, decisions, specifications, progress, and verification instructions without waiting for a separate documentation request. Keep explicit proposed/accepted status and preserve historical evidence.

Use one work brief for both implementation scope and the developer handoff. QA records the exact tested revision, acceptance coverage, defects, and limitations. No empty report is presented as executed QA, and developer checks are not labeled independent review.

## Consequences

Documentation changes travel with the behavior or process change that caused them. The user remains the authority for unresolved product choices; routine technical decisions proceed within delegated scope. Adopting the documents does not automatically accept every technical proposal or authorize deployments.

Roles do not require agents to run simultaneously. When parallel work is authorized, use isolated worktrees/branches and explicit handoff revisions. There is no separate issue tracker or duplicated backlog at this stage.

## References

[AGENTS.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/AGENTS.md?type=file&root=%252F); [development-process.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/development-process.md?type=file&root=%252F); [strategy.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/strategy.md?type=file&root=%252F). This record replaces the setup proposal with the maintained working process.
