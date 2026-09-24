# W025 developer verification — external food catalog fallback

Revision: commits `5becd00`, `ea8bf24`, and `556836d` plus the conflicting-identity fallback fix (before its local commit).
Date: 2026-09-24. Reviewer: lead assistant (developer verification).

The adapter tests cover injected Open Food Facts and USDA nutrient mapping,
invalid/empty results, provider failure continuation, and composite deduplication.
The PostgreSQL worker test covers an unknown product becoming an unconfirmed
candidate, durable numbered selection, immutable source provenance with a
separate `product_confirmations` row, deterministic food persistence after
selection, and reuse of the confirmed local version without a second provider
call. Migration/model drift, the full integration suite, the retained QA suite,
the offline suite, dependency checks, and whitespace checks passed.

The follow-up resolver-context fix and the identity-only unresolved-food fallback
were rerun through the full offline suite and PostgreSQL suites; all passed. The
worker tests cover `Съела 80 гр творога 2,5%` both as a model proposal with only
the food identity unresolved and as a proposal that selected a conflicting local
identity. In both cases the configured lookup receives the bounded food term and
a numbered candidate clarification is created without a food mutation.

Executed evidence:

- `tests.test_food_sources`: 4 passed.
- `tests.integration` (with `PYTHONPATH=tests/integration`): 106 passed.
- `tests.qa` (with `PYTHONPATH=tests/qa`): 32 passed.
- `tests`: 122 passed.
- `pip check`: no broken requirements.
- `git diff --check`: clean after the final test-file formatting fix.

No independent QA review was run. A user-run live Open Food Facts search for
`творог 2,5%` returned HTTP 503 on 2026-09-24; the worker consequently kept
the message retryable as `food_source_unavailable` without a food mutation.
Provider availability, live payload drift, quotas, and production Russian
search quality therefore remain unverified. Restaurant nutrition, barcode/photo
flows, and background synchronization remain outside W025.
