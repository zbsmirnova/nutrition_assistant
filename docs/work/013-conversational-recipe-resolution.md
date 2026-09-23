# W013 — Conversational saved-recipe lookup and consumption

Status: done.
Milestone: M3.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D023.

## Outcome and scope

Allow an ordinary food message to select a user's saved recipe and log explicit eaten grams through the existing pinned `RecipeComponent` path. Expose only opaque recipe references to the parser, resolve ownership and version IDs in the backend, and leave duplicate named matches unresolved.

This slice does not implement recipe aliases or inflection-aware search, recipe clarification/resumption, recipe-aware corrections, multi-action recipe creation plus consumption, external database comparison, or live model quality measurement.

## Requirements and decisions

RECIPE-002/RECIPE-003, CALC-001, DATA-002, and DATA-003 apply. D021 and D022 provide the recipe persistence and pinned-consumption foundations; D023 defines the conversational lookup boundary. The accepted model stores no recipe portion or cooked-batch entity.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W013-A01 | The worker exposes current owned recipes as parser candidates with only `ref` and `name`; private recipe/version IDs are absent from the parser request and Nebius payload. |
| W013-A02 | An explicit scoped recipe candidate plus exact positive grams creates a normal food entry using the selected pinned recipe version and backend-scaled nutrition. |
| W013-A03 | A unique named recipe can be resolved without a database ID in the proposal and uses the current owned recipe version. |
| W013-A04 | A missing or duplicate named recipe match remains unresolved without a food mutation; duplicate names can still be selected through an explicit scoped candidate. |
| W013-A05 | Existing offline, PostgreSQL integration, retained QA, and diff checks pass; no live provider or Telegram claim is added. |

## Implementation checklist

- [x] Add bounded recipe candidates to worker context, parser request, Nebius projection, and response validation.
- [x] Resolve unique names and explicit recipe refs into pinned `RecipeComponent` commands.
- [x] Preserve ambiguity and quantity/evidence safeguards without creating food.
- [x] Add integration coverage for explicit, unique-name, and ambiguous-name paths.
- [x] Update decision, specification, roadmap, README, and QA evidence.

## Developer handoff

Implementation revision: the final local commit is recorded in the linked developer QA report after closeout.

The worker queries current user-owned recipe versions, projects opaque refs, and constructs the existing typed recipe component only after backend resolution. The parser contract models were unchanged, so schema regeneration was not required. See the linked developer report for exact commands and results.

Known limitations are intentional: live Nebius interpretation, natural-language aliases/inflection, clarification UX, recipe corrections, and external comparison remain unverified or future scope.

## QA result and completion

Developer verification is recorded in [013-conversational-recipe-resolution-developer.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/qa/reports/013-conversational-recipe-resolution-developer.md?type=file&root=%252F). No independent W013 review was run.
