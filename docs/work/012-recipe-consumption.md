# W012 — Consume saved recipes by eaten grams

Status: in progress.
Milestone: M3.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D022.

## Outcome and scope

Allow a resolved `RecipeComponent` to be logged as food with explicit eaten grams. Pin the selected recipe version, calculate nutrition in the backend, and preserve the normal food-entry/day revision and retry behavior.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W012-A01 | A recipe component with positive eaten grams creates a normal food entry and daily totals from the pinned recipe version. |
| W012-A02 | Recipe and product food components are explicitly distinguished in storage; recipe components do not require product IDs or product weight basis. |
| W012-A03 | Revising a recipe changes only future consumption; earlier food entries retain their original recipe version and nutrition snapshot. |
| W012-A04 | Missing, foreign, or stale recipe versions are rejected without a food mutation; retries remain idempotent. |
| W012-A05 | Migration, offline, integration, retained QA, and schema-drift checks pass. |

## Boundaries

This slice does not implement natural-language recipe lookup, recipe clarification, recipe-aware conversational corrections, volume-density resolution, or external database comparison.
