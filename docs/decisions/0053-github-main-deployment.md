# D053 — GitHub `main` deployment for the private pilot

Kind: technical.
Status: accepted for MVP deployment.
Recorded: 2026-09-26.
Decision owner: product owner delegated the deployment goal; architect chose
the implementation within the single-host constraint.
Related decisions: D040, D049.

## Context

The Netcup pilot was initially installed from a manually uploaded source
archive. There is no CI/CD workflow in the repository, so a change on GitHub
does not reach the running worker automatically. Runtime credentials must stay
on the host, and the 2 GB VPS should not gain a registry, web service, or extra
runtime component just to deploy a small private application.

## Decision

Use GitHub Actions for a two-job `main` pipeline:

1. run the pinned offline, PostgreSQL integration, and retained QA suites;
2. only after those pass, archive the exact tested commit and upload it over a
   dedicated SSH key;
3. unpack it under `/opt/nutrition_assistant/releases/<commit>` and run the
   existing production Compose topology with the host's unchanged `.env`;
4. build the migration/worker images, run migrations, start the worker, and
   wait for its Docker health check before marking deployment successful.

The workflow also supports a manual dispatch, but deployment remains restricted
to the `main` ref. A concurrency group allows only one production deployment at
a time. Runtime Nebius, Telegram, and PostgreSQL secrets remain in the server's
untracked `.env`; GitHub receives only deployment SSH material and host
connection settings.

## Alternatives and consequences

Building and uploading the source keeps this one-host MVP simple and avoids
private GHCR credentials or a second registry lifecycle. It uses some CPU on
the VPS during an upgrade and does not provide an automatic rollback. Previous
release directories remain available for a manual rollback, subject to the
usual database-migration compatibility check.

This does not replace the required backup/restore rehearsal in W024 and does
not claim zero-downtime deployment. A failed migration stops the deployment
before the worker is replaced; a failed health check requires operator review.

## References

[W024](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/024-mvp-pilot-deployment.md?type=file&root=%252F),
[D040](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0040-private-mvp-pilot-deployment.md?type=file&root=%252F),
[ci-cd.yml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/.github/workflows/ci-cd.yml?type=file&root=%252F),
and [deploy-production.sh](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/scripts/deploy-production.sh?type=file&root=%252F).
