# D006 — Decimal arithmetic, bounds, and persisted totals

Kind: technical.
Status: accepted for M1.
Recorded: 2026-09-22.
Decision owner: lead architect under delegated implementation authority.
Related question: Q03 resolved for M1.
Acceptance evidence: implementation decision preserving CALC-001/CALC-002 and the existing decimal-string contract limits.

## Decision

Use finite nonnegative Decimal values and numeric(18,6) storage. The supported maximum is 999999999999.999999; physical quantities must be positive where required by the contracts. Reject overflow explicitly and roll back the mutation; never truncate, clamp, or switch to floating point.

Calculate with decimal precision 64, retaining intermediate precision. Scale a pinned per-100-g profile only by compatible edible grams, or a per-100-ml profile only by compatible millilitres. Require the raw/cooked/as-sold basis to match. Missing conversions are errors to resolve before execution; never assume 1 ml equals 1 g.

Quantize each persisted consumed-component nutrient and its supplied bounds once to six fractional digits using round-half-up. Aggregate those persisted component values for entry/day totals, so results can be reproduced exactly from saved records. Presentation rounding is a separate future renderer concern.

Small values can round to zero at the declared storage resolution; this does not convert unknown data to zero. For example, two separate scaled values of 0.0000005 each persist as 0.000001 and sum to 0.000002. This is an explicit component-rounding policy rather than silently mixing rounded and unrounded totals.

Unknown nutrients remain NULL. A partially known entry nutrient remains unknown in its complete-value snapshot; day results expose known subtotal and component coverage. Wholly unknown and empty totals have distinct result variants. Explicit supplied zero remains a known value.

Retain aggregate lower/upper bounds only when every known contributing value in that complete total has bounds. Do not fabricate bounds for unbounded source values. Bounds remain working estimates, not statistical confidence intervals.

## Consequences and evidence

Component and daily overflow checks are necessary even when every source value fits its column. Calculations retain a policy version, decimal-components-v1, alongside source and quantity evidence. Recipe normalization, user-confirmed estimates, and additional conversions remain later work; this record does not claim those engines exist.

Implementation: [nutrition.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/nutrition.py?type=file&root=%252F). Checks: [test_nutrition.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/test_nutrition.py?type=file&root=%252F) and [test_food_service.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/tests/integration/test_food_service.py?type=file&root=%252F). The latter verifies that day-total overflow leaves no second mutation or success response.
