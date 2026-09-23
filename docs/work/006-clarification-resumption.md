# W006 — Resume one pending dairy clarification

Status: in QA.
Milestone: M2.
Owner: lead assistant, architect/developer; independent QA pending.
Updated: 2026-09-23.

## Outcome and scope

Turn W003's unresolved dairy-fat result into a resumable one-question workflow. For `Съела 100 г творога` followed by a Telegram reply `5%`, keep the original 100 g and source date, validate the typed answer, save one food entry, and clear the pending count. Replaying the answer must not create another entry.

This slice is intentionally bounded to one active dairy-fat question identified through Telegram reply-to metadata. It does not implement mixed-message partial saving, several simultaneous questions, bare-number quantity answers, cancellation, corrections/delete/undo, or live model quality.

## Requirements and decisions

FOOD-001/FOOD-002/FOOD-003, DATA-002/DATA-003, CALC-001, and D010 govern the behavior. D015 defines the temporary question-state representation and operation/evidence reuse. The parser remains untrusted; the backend owns the original date, candidate scope, product identity, command identity, arithmetic, and writes.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W006-A01 | An unresolved dairy message stores a typed pending question map and no food mutation. |
| W006-A02 | A reply to the exact original Telegram message is given only the scoped pending candidate/question context; an unrelated reply remains `conversation_context_required`. |
| W006-A03 | A valid typed nutrition answer re-resolves the frozen original proposal, retaining the original quantity/date and using the answer only as product evidence. |
| W006-A04 | The trusted command uses the original operation ID, original update first in evidence, answer update second, and the pending conversation job as its pending-action reference. |
| W006-A05 | Preparation, execution, crash recovery, and replay produce at most one food entry/outbox result; the original pending job is cleared after successful application. |
| W006-A06 | Invalid answer token/type, missing pending target, or incomplete fat answer remains deferred/rejected without a food mutation. |
| W006-A07 | Existing standalone-food, forwarded/reply-without-pending, provider retry, ownership, and schema checks remain green. |

## Implementation checklist

- [x] Add migration/schema state for pending question maps.
- [x] Expose pending context through the provider-neutral parser request and Nebius payload only when active.
- [x] Re-resolve one dairy-fat answer against frozen original evidence and preserve operation/date/evidence identity.
- [x] Allow the existing food service to validate pending clarification evidence and clear the original pending job after success.
- [x] Add offline and PostgreSQL integration coverage for answer, replay, and pending cleanup.
- [ ] Run database integration and independent QA on the completed revision.
- [ ] Update the report with exact revision and coverage limits, then commit the completed slice.

## Developer handoff

Working implementation is in the current worktree on top of the prior clean revision. Offline contract/resolver/provider tests pass (`96` tests). PostgreSQL integration is required for the migration, job-link, crash, and idempotency criteria; the current sandbox cannot connect to the documented local PostgreSQL port without escalation.

## QA result and completion

Not yet complete. Independent QA and PostgreSQL execution are pending. No live Nebius or real Telegram behavior is claimed.
