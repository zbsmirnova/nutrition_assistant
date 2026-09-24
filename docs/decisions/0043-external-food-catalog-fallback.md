# D043 — External food catalog fallback for MVP cold start

Status: accepted for MVP pilot. Recorded 2026-09-24 by the product owner and lead assistant.

The personal catalog remains the first lookup boundary. When a food name is
not found locally, the worker may query configured external catalog adapters
with the normalized food term. The provider result is an untrusted candidate,
never a food entry and never an authorization to use nutrition values.

The worker stores the provider snapshot and asks the user to choose a candidate.
It then asks for the exact eaten weight or an explicit user-approved estimate,
using the existing MVP quantity rule. Only the selected candidate and the
approved portion can enter a daily total. The source snapshot is immutable;
the user's selection is recorded in a separate confirmation row. A confirmed
version becomes part of the user's local catalog and later messages use it
without another provider request.

The MVP adapter set is Open Food Facts for packaged/branded and multilingual
coverage, plus USDA FoodData Central when `USDA_FDC_API_KEY` is configured for
generic food references. Their licenses and source identifiers are retained in
the source evidence. Provider failure is retryable; an empty or unsuitable
result stays unresolved. Unknown restaurant nutrition remains pending until a
separate nutrition-source decision is made. No barcode, photo, restaurant
estimate, bulk import, or automatic background synchronization is included.

This supersedes D020's blanket deferral of runtime external lookup for the MVP;
its deterministic recipe comparison and offline evaluation constraints remain
in force where this fallback does not apply.

The trade-off is one or two extra user turns for a previously unknown product,
in exchange for avoiding silent provider choice and keeping the personal
catalog reusable after the first confirmation.
