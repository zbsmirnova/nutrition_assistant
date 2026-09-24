# W024 — Always-on MVP pilot runner and deployment

Status: in progress.
Milestone: M6 personal release readiness, first usable MVP pilot.  
Owner: lead assistant, architect/developer.  
Decision: D040; Q10/Q11 constraints remain open.

## Goal

Make the already tested personal MVP usable without manually invoking
`telegram-process` for every message. Deploy one private worker and PostgreSQL
on an always-on host while preserving the durable inbox, job, revision, and
outbox boundaries.

## Scope

1. Add a long-running one-owner Telegram worker with graceful SIGTERM handling,
   bounded idle polling, provider-error backoff, and no competing pollers.
2. Add an application production image and a Compose deployment containing the
   worker, PostgreSQL, migration startup, persistent storage, and health checks.
3. Document secret injection, first startup, upgrade/rollback, log redaction,
   and operator smoke checks. Keep credentials and personal messages out of
   tracked files.
4. Add encrypted PostgreSQL dump and restore-rehearsal instructions. Record
   the actual backup evidence before claiming personal-release readiness.
5. Run the live pilot acceptance path: food, recipe clarification, weight,
   steps, correction, retry/restart, and Telegram delivery.

## Out of scope

Reminders, callbacks, close-day behavior, scheduled check-ins, Apple Health,
feedback capture, public HTTP/API access, multi-user dispatch, horizontal
scaling, and unknown-restaurant nutrition sourcing.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W024-A01 | A supervised worker continues polling after an empty poll and after a recoverable provider/database failure, with bounded backoff and no duplicate claimers. |
| W024-A02 | SIGTERM stops polling cleanly; an in-flight durable job/outbox item can be recovered by the next start. |
| W024-A03 | A clean host startup runs the required migration and starts the worker without exposing PostgreSQL or an application HTTP port publicly. |
| W024-A04 | Secrets are supplied outside the image and repository; normal logs contain statuses/IDs only and no message text or tokens. |
| W024-A05 | A backup can be restored into a disposable PostgreSQL instance and the application resumes from the restored durable state. |
| W024-A06 | The live pilot acceptance scenarios pass on the selected host; each result records its revision, limits, and whether it was developer or independent QA evidence. |

## Required user input before deployment

The product owner selected a Netcup VPS nano G11.5s: 2 vCore x86, 2 GB RAM,
60 GB SSD, public IPv4/IPv6 connectivity, and a six-month term. This is an
explicit single-user pilot constraint; the production image limits the worker
and database for the small host, and the host must use swap. Extra IPv4 and
Cloud vLAN are not required. Upgrade to 4 GB RAM remains the recovery path if
the pilot shows memory pressure. Credentials are entered directly into the
host's secret store and must not be sent in chat or committed.
