# D040 — Private single-host MVP pilot deployment

Status: Accepted for MVP topology; provider not selected
Recorded: 2026-09-24
Authority: product-owner choice of always-on cloud; hosting provider and spending constraints remain open
Related questions: Q10, Q11

## Decision proposal

For the first usable deployment, run one private application worker and one
PostgreSQL instance on an always-on EU VPS using Docker Compose. The Telegram
bot uses long polling, so the pilot needs no public HTTP endpoint. Nebius and
Telegram are outbound dependencies; SSH is the only administrative entry
point.

The worker is single-replica and is restricted to the configured internal user
and allowlisted private Telegram account. PostgreSQL stays on the private
Compose network with a persistent volume. The host supervises the worker and
restarts it after failure. Automatic scale-to-zero or auto-stop is not allowed
for this process.

Secrets are injected through the host environment or root-readable secret
files: `NEBIUS_API_KEY`, `NUTRITION_LLM_MODEL`, `NUTRITION_TELEGRAM_TOKEN`,
`NUTRITION_TELEGRAM_BOT_ID`, and the internal user configuration. They are not
stored in the image, Compose file, repository, or ordinary logs.

The host performs an encrypted daily PostgreSQL dump to storage separate from
the VPS. A restore rehearsal is required before calling the pilot release
ready. Retention, export, deletion, provider data sharing, and the exact
backup target/retention remain Q10/Q11 decisions; this proposal does not make
them silently accepted policy.

## Why this is the MVP boundary

The application is currently one modular Python worker plus PostgreSQL. A VPS
keeps the process alive at low operational complexity and avoids introducing
Kubernetes, Redis, a public API, webhooks, or a second service. The existing
`compose.dev.yml` is local development only. The current `Dockerfile` and
`fly.toml` describe the legacy Open WebUI deployment and must not be reused for
this application.

Before deployment, W024 must add a long-running worker command with graceful
shutdown and bounded error backoff. The existing `telegram-process` command is
an operator one-shot and must remain useful for local diagnostics; wrapping it
in an unbounded shell loop is not the production contract.

This is a personal pilot decision. Multi-user access, public onboarding,
webhook transport, horizontal replicas, managed database migration, reminders,
and feedback capture remain outside MVP.

## Alternatives considered

- **Keep the Mac as the host:** no hosting cost, but the bot stops when the
  laptop sleeps, loses network, or the terminal environment changes. Keep only
  as a temporary fallback.
- **Reuse the existing Fly/Open WebUI files:** rejected because they launch a
  different application and allow zero running machines, which is incompatible
  with long polling.
- **Managed services/Kubernetes:** deferred; they add cost and operational
  surface without helping a single-user MVP.

## Remaining choice

The product owner selected Hetzner Cloud in Germany. CX23 is the preferred
shape (2 vCPU, 4 GB RAM, 40 GB local storage), but it is currently unavailable
in the console. Provision the first currently available x86/AMD plan with at
least 2 vCPU and 4 GB RAM; CPX22 (2 vCPU, 4 GB, 80 GB) or CX33 (4 vCPU, 8 GB,
80 GB) are acceptable fallbacks if offered. Do not choose an ARM CAX plan
without a separate compatibility check. Actual deployment requires a separate
authorized operation after W024 is implemented, tested, and the secrets are
provided through the host's secret mechanism. Backup retention, restore target,
and final availability objective remain open under Q10/Q11.
