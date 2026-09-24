# D041 — Cold-start cloud alternative for the MVP pilot

Status: Rejected for MVP; retained as a later alternative
Recorded: 2026-09-24
Authority: architect recommendation for product-owner choice
Related questions: Q10, Q11

## Architecture required by cold start

The current `getUpdates` long-polling worker cannot wake a stopped container.
This option requires Telegram `setWebhook` over public HTTPS. The webhook
handler must authenticate the Telegram secret header, persist the update into
the existing durable inbox, return `2xx` quickly, and let an asynchronous job
worker perform interpretation, resolution, writes, and outbox delivery. The
database must remain persistent while the application container sleeps. Only
one worker instance may consume the bot.

This preserves the existing database/job/outbox model, but adds a public
webhook endpoint, retry/idempotency tests, deployment TLS, and a second runtime
path. Telegram webhook and `getUpdates` cannot be active at the same time.

## Resource envelope

- webhook/worker: 0.25–0.5 vCPU and 512 MB RAM minimum; 1 GB is a safer first
  production setting. No GPU is needed because inference runs in Nebius;
  maximum instances must be one;
- PostgreSQL: persistent 1 shared vCPU, 512 MB–1 GB RAM, and 5–10 GB storage
  for this single-user dataset;
- backup: separate object storage or provider backup, with a restore rehearsal;
- network: public HTTPS ingress for Telegram and outbound HTTPS to Telegram and
  Nebius; keep PostgreSQL private.

## Provider shortlist (prices checked 2026-09-24)

- **Fly Machines:** closest fit technically. Machines support auto-stop and
  auto-start on incoming traffic. The published shared presets start at about
  $1.94/month for 256 MB and about $3–4/month for 512 MB when running; stopped
  machines are charged for rootfs at $0.15/GB-month, with volumes priced
  separately. This is low cost and portable, but backups and PostgreSQL
  operations remain our responsibility. See the official [Machines pricing](https://fly.io/pricing/)
  and [autostop/autostart](https://www.fly.io/docs/launch/autostop-autostart/).
- **Railway:** easiest developer experience. Hobby is $5/month with $5 of
  included resource usage; RAM is $10/GB-month, CPU $20/vCPU-month, and volume
  storage $0.15/GB-month. Serverless mode sleeps an inactive service after no
  outbound traffic and wakes it for a new request, so it requires webhook
  transport rather than polling. See [Railway pricing](https://docs.railway.com/pricing)
  and [serverless mode](https://docs.railway.com/deployments/serverless).
- **Google Cloud Run:** most mature serverless option, but the most setup
  overhead. The default minimum is zero instances. The free tier includes
  240,000 vCPU-seconds, 450,000 GiB-seconds, and 2 million requests per month;
  region and networking affect the bill. A separate persistent PostgreSQL
  service is still required. See [Cloud Run pricing](https://cloud.google.com/run/pricing)
  and [minimum instances](https://docs.cloud.google.com/run/docs/configuring/min-instances).

Supabase can supply PostgreSQL for a prototype: its free plan includes 500 MB
and may pause projects after a week of inactivity; Pro starts at $25/month and
includes daily backups with seven-day retention plus compute credits. It is not
a zero-cost always-available production database. See [Supabase pricing](https://supabase.com/pricing)
and [project pausing](https://supabase.com/docs/guides/platform/free-project-pausing).

## Recommendation

For a cold-start experiment, prefer **Railway** for the easiest first setup or
**Fly Machines** for lower cost and more control. Cloud Run is technically
sound but disproportionate for this one-user MVP. The database cost and
webhook implementation dominate the savings, so cold start should be chosen
for an explicit low-idle-cost goal, not assumed to be simpler than one small
always-on VPS.
