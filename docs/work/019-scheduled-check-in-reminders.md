# W019 — Scheduled check-in reminders after MVP

Status: planned.
Milestone: M5 post-MVP.
Owner: lead assistant, architect/developer.
Updated: 2026-09-23.
Depends on: W018 dinner-triggered check-in, D031 MVP scope decision.

## Outcome and scope

Add the optional scheduled check-in reminder that is deliberately excluded from MVP. When enabled and no dinner check-in has been offered for the local day, the service may create one local-time fallback offer, initially proposed for 21:00. It must share the same daily-check-in identity and suppression rules as the dinner-triggered offer.

The reminder path must not create a second offer after a late dinner, after conversational closure, or after a retry. A missed occurrence is not silently replayed on a later day.

## Proposed architecture to decide before implementation

- A database-backed scheduler process polls due users every 30–60 seconds and uses a PostgreSQL advisory lock so only one planner creates an occurrence at a time.
- Each intended reminder has an occurrence key scoped to the user and local date, such as `fallback:{user_id}:{local_date}`. A unique database constraint, rather than a worker attempt, defines one logical occurrence.
- The scheduler converts the current instant through the user's IANA time zone. DST behavior, including repeated or nonexistent local times, must be specified and tested before release.
- `notification_rules` stores the enabled local time and version. `notification_runs` records the intended occurrence and its status. The scheduled message enters the same durable delivery path as ordinary Telegram replies through a generalized scheduled-outbox model or an explicitly chosen equivalent.
- Dinner-triggered check-ins and reminder-triggered check-ins share `daily_check_ins`; whichever is committed first suppresses the other. Telegram callback actions reuse W018's server-side opaque callback binding and stale-state validation.
- If the service is offline after the intended local time, the missed occurrence expires for that local date. The scheduler does not send a backlog of old reminders.

These are design proposals, not accepted technical decisions. Record the final scheduler, DST, outbox, and outage choices before implementation.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W019-A01 | An enabled user receives at most one fallback offer for a local date when no dinner offer exists and the local reminder time is reached. |
| W019-A02 | A dinner offer, closure, or completion suppresses a not-yet-sent fallback for that date. |
| W019-A03 | A late dinner after a fallback reuses the same daily-check-in identity and creates no second offer. |
| W019-A04 | Repeated scheduler polls, process restarts, and concurrent planner claims cannot create duplicate logical occurrences. |
| W019-A05 | DST transition cases produce the specified local-date behavior; missed occurrences are not replayed after an outage. |
| W019-A06 | Scheduled messages use durable retry/lease/uncertain-send handling, and callback actions reject stale, foreign, or already-consumed tokens. |

## Out of scope

This work does not change the MVP dinner-triggered check-in, add new activity metrics, or decide weekly-report content and scheduling. It does not promise exactly-once visible Telegram delivery.

## Readiness

Not started. First create the technical decision that resolves the proposed scheduler, DST, occurrence-key, scheduled-outbox, and outage policies. Then implement migration, planner, delivery integration, and retained PostgreSQL/Telegram protocol tests.
