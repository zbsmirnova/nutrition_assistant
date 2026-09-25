# W021 — Local product provisioning for the MVP pilot

Status: done.
Milestone: M2 pilot setup.
Owner: lead assistant, architect/developer.
Decision: D035.

## Outcome

Add a trusted local operator command that creates one owner-scoped product version from explicitly supplied nutrition values. This is the seeded-fixture path for the MVP validation gate: it supplies the bounded catalog context needed to test a live Telegram food save without allowing the model to invent nutrition or product identity. Telegram product creation is a later catalog-growth slice after the gate.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W021-A01 | `product-create` requires an owner UUID and product name, validates supplied non-negative nutrition, and creates a user-owned immutable product version. |
| W021-A02 | The product is pinned to an `operator_catalog` provenance record; no parser or provider call can create catalog data. |
| W021-A03 | Invalid empty nutrition, food kind, basis, or dairy percentage is rejected before mutation. |
| W021-A04 | Existing contract, worker, Telegram, and migration behavior remains unchanged. |

## Usage

```sh
.venv/bin/python -m nutrition_app product-create \
  --user "$INTERNAL_USER_ID" \
  --name "Яблоко" \
  --kcal 52 --protein-g 0.3 --fat-g 0.2 --carbs-g 14
```

Values are entered per 100 g by default. Use `--nutrition-basis per_100_ml` for volume products, and use `--food-kind dairy --declared-fat-percent N` when a dairy label percentage is known.

## Verification

Developer verification: the complete offline suite passed (`112` tests), and the dedicated PostgreSQL provisioning checks passed (`2` tests) against a disposable schema. The user then ran the command for an apple profile and verified one live Telegram food message with `status: applied` and `delivery: sent`; the bot returned the expected scaled nutrition. One previously unresolved unmatched message remained pending. No independent QA review was run.
