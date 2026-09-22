# D003 — Modular application and relational revision storage

Kind: technical.
Status: accepted for M1.
Recorded and updated: 2026-09-22.
Decision owner: lead architect under delegated implementation authority.
Acceptance evidence: the user authorized implementing the first food-persistence slice; the original brief proposed Python/PostgreSQL. The specific local libraries and schema are the architect's technical choices.
Related questions: Q01/Q02 resolved for M1; numeric policy is D006.

## Decision

Use one modular Python application and PostgreSQL. M1 uses SQLAlchemy Core 2.0.54 for explicit relational operations, psycopg 3.3.6, and Alembic 1.20.0 for frozen migration history. Dependencies are pinned in [requirements-runtime.txt](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/requirements-runtime.txt?type=file&root=%252F); no ORM session or separate service framework is needed for this slice.

The verified local runtime is Python 3.14.0 and PostgreSQL 17.11. Python 3.12+ remains the intended minimum, but this is not a claim of a multi-version test matrix. [compose.dev.yml](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/compose.dev.yml?type=file&root=%252F) pins the pulled PostgreSQL image digest, binds only to localhost, and preserves development data in a named volume.

Store stable entities with owned current pointers to immutable ordinary revisions/versions. Deferred composite foreign keys prove each current revision/version belongs to its logical parent and user. Snapshot-update triggers protect sources, messages, commands, results, nutrition versions, and food revisions/components; ordinary erasure policy remains a separate requirement.

Keep queried quantities/nutrients/dates/ownership in typed columns. Store frozen command/result/evidence payloads as versioned JSON. Food components retain pinned source/version, normalized edible mass or volume, optional gross/inedible mass, and calculation policy. Derive daily totals from current active component snapshots initially.

## Physical scope

M1 implements 13 domain/operational tables plus Alembic's version table. They cover users/accounts, inbox, prepared/applied operations, sources/products/versions, food days/entries/revisions/components, and outbox. It does not provision recipe, observation, clarification, report, or scheduler tables in advance.

The full logical model remains in [data-model-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/data-model-v1.md?type=file&root=%252F); its M1 subsection identifies physical differences. Runtime declarations are in [schema.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/nutrition_app/schema.py?type=file&root=%252F); the two migrations are [0001_m1_food_persistence.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/migrations/versions/0001_m1_food_persistence.py?type=file&root=%252F) and [0002_bot_delivery_identity.py](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/migrations/versions/0002_bot_delivery_identity.py?type=file&root=%252F). The second preserves existing source rows while strengthening delivery identity to bot scope.

Every integration test uses a fresh random schema with no fallback to public. The suite verifies fresh migration, repeat upgrade, downgrade/upgrade in its own disposable schema, metadata drift, and ownership/current-pointer constraints.

## Alternatives and consequences

Full event sourcing adds replay/evolution complexity without a demonstrated requirement. Document-only storage weakens relational integrity. Microservices/Redis introduce operational work that is unnecessary for M1.

Ordinary snapshots consume storage and need explicit deletion/retention design. Decimal precision and rounding are defined separately in D006. Application actor checks and composite foreign keys are present; RLS and a runtime role unable to bypass it remain required before broader user access. The local CLI is trusted tooling, not a public authentication boundary.

Independent QA is a separate status tracked by the work brief; passing contract shapes alone never establishes database correctness.
