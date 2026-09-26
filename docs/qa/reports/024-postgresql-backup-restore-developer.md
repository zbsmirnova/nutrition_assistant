# W024 — PostgreSQL backup and restore rehearsal

Status: developer verification passed.
Date: 2026-09-26.
Environment: Netcup single-user pilot; production `db` and `worker` were
healthy before the rehearsal. No independent QA review was run.

## Evidence

- `pg_dump --format=custom --no-owner --no-acl` completed from the production
  PostgreSQL container.
- The dump was encrypted temporarily with AES-256-CBC and PBKDF2 before the
  restore test. The encrypted artifact was 99,488 bytes with SHA-256
  `0561de9a4cdca45dd7039835d0ab03d99976832d31f32646c9493571e46e44a3` and
  contained 188 restore TOC entries.
- The dump was decrypted into a disposable PostgreSQL 17 container on the
  private Compose network and restored with `pg_restore --exit-on-error`.
- The restored database reported Alembic version `0010`, one user, nine
  products, and one food day.
- The current application image connected to the restored database through
  `db-info`, returning PostgreSQL `17.11` and schema `public`.
- The disposable container, plaintext dump, encrypted rehearsal artifact, and
  in-memory rehearsal passphrase were removed after verification. The
  production volume and worker were not modified.

The first attempt stopped before the application check because Docker was
given an internal image ID instead of its local image name; cleanup ran and a
second attempt completed the full rehearsal. This did not change production
data.

## Limits

This proves restore into a disposable instance and application connectivity,
not an operational backup-retention policy. The encryption passphrase was
intentionally ephemeral for this rehearsal. Off-host storage, retention,
key-management, and restore objectives remain the open Q10/Q11 decisions.

This is developer evidence for W024-A05, not an independent QA verdict.
