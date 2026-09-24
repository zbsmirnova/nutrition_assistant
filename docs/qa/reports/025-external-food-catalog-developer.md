# W025 developer verification — external food catalog fallback

Revision: working-tree snapshot after the W025 implementation (before commit).
Date: 2026-09-24. Reviewer: lead assistant (developer verification).

The adapter tests cover injected Open Food Facts and USDA nutrient mapping,
invalid/empty results, provider failure continuation, and composite deduplication.
The PostgreSQL worker test covers an unknown product becoming an unconfirmed
candidate, durable numbered selection, immutable source provenance with a
separate `product_confirmations` row, deterministic food persistence after
selection, and reuse of the confirmed local version without a second provider
call. Migration/model drift, the full integration suite, the retained QA suite,
the offline suite, dependency checks, and whitespace checks passed.

Executed evidence:

- `tests.test_food_sources`: 4 passed.
- `tests.integration` (with `PYTHONPATH=tests/integration`): 104 passed.
- `tests.qa` (with `PYTHONPATH=tests/qa`): 32 passed.
- `tests`: 122 passed.
- `pip check`: no broken requirements.
- `git diff --check`: clean after the final test-file formatting fix.

No independent QA review was run. No live Open Food Facts or USDA request was
made, so provider availability, live payload drift, quotas, and production
Russian search quality remain unverified. Restaurant nutrition, barcode/photo
flows, and background synchronization remain outside W025.
