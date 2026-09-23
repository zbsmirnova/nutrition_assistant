# W020 — Bounded Telegram MVP processing loop

Status: done.
Milestone: M2 (MVP pilot tooling; does not add post-MVP scheduling).
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Decision: D034, using W002 transport, W003 worker, W004 Nebius adapter, and D033 backend-derived evidence.

## Outcome and scope

Add one explicit `telegram-process` command that polls one bounded batch, processes the next eligible message for one supplied owner through Nebius, and dispatches one queued response. Keep polling, interpretation, durable job claims, retries, and outbox delivery as their existing separate components. Do not add a daemon, scheduler, callback keyboard, close-day command, or multi-user dispatcher.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W020-A01 | The command requires an owner UUID, validates the bot configuration, polls with the requested bounded timeout, and does not print credentials or source text. |
| W020-A02 | It invokes the existing worker without an explicit source so the worker selects the owner's oldest eligible job and preserves durable claim/retry behavior. |
| W020-A03 | It dispatches one queued response through the existing Telegram sender and reports only poll, processing, and delivery status. |
| W020-A04 | Existing commands and the separate synthetic/fake paths remain unchanged. |
| W020-A05 | Focused CLI/protocol tests and the complete offline suite pass; no live Telegram or model result is claimed. |

## Implementation and verification

- [x] Add the `telegram-process` CLI composition.
- [x] Keep output redacted to operational status fields.
- [x] Add the D034 decision and README operator instructions.
- [x] Run focused Nebius/CLI tests and the complete offline suite.

Developer verification: focused Nebius/CLI tests passed, followed by 111 offline tests. No independent QA review, live Telegram delivery, or live model quality result was run for this slice.

## Usage

~~~sh
.venv/bin/python -m nutrition_app telegram-process --user INTERNAL_USER_UUID --timeout 25
~~~

Repeat the command to process another message or retry a durable job. Use the separate commands when diagnosing a specific source or delivery state.
