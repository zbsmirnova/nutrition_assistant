# W027 runtime cleanup and readback verification

Revision: `f239c7c` (`Clean MVP runtime and add durable day readback`).
Date: 2026-09-25.
Role: developer verification by the lead assistant.
Independent QA review of this revision: not run as a separate review.

## Changes covered

- The production CLI and long-running pilot runner no longer construct an
  external Open Food Facts/USDA lookup. The optional adapter code remains
  isolated for the later unknown-food experiment.
- `get_day_summary` now resolves a backend-owned date, freezes a typed command,
  stores the result and Telegram outbox payload, and renders only kcal and
  protein in the MVP reply.
- Replay of the read operation does not call the parser again.

## Checks

| Check | Result |
| --- | --- |
| Offline contract/unit suite | 124 passed |
| PostgreSQL integration suite | 107 passed |
| Retained independent QA suite | 32 passed |
| New resolver/render tests | Included in the 124 offline tests |
| New durable worker readback test | Included in the 107 integration tests |
| `git diff --check` | passed |

The database suites used the local PostgreSQL test service with disposable
schemas. No live Nebius request or Telegram send was made by these checks.
Live model interpretation quality, real Telegram delivery for day readback,
and the complete W027 scenario scorecard remain open.

## Result

Developer verification passes for this slice. W027 remains `in progress` until
the full seeded-catalog gate and its separate live-model/Telegram evidence are
recorded.
