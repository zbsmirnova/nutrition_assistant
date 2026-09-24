# D035 — Trusted local product provisioning for the MVP pilot

Status: accepted for MVP pilot setup.
Date: 2026-09-24.
Owner: architect/developer under delegated implementation authority.

The first live Telegram pilot may use a trusted local `product-create` operator command to add an owner-scoped product with explicitly supplied nutrition values per 100 g or 100 ml. The command creates an immutable product version and an `operator_catalog` provenance record. The model cannot create or mutate catalog rows, and no external database is queried by this path.

This keeps food calculation backend-owned and gives the pilot a known catalog item for end-to-end testing. User-facing catalog editing, label capture, external catalog lookup, aliases, and product revisions remain later work. Unknown or unmatched foods stay unresolved and are not saved.

Related work: [W021](../work/021-local-catalog-provisioning.md), [W004](../work/004-nebius-adapter.md), and [W020](../work/020-telegram-processing-loop.md).
