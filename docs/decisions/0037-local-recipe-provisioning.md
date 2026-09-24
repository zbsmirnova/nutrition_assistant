# D037 — Trusted local recipe provisioning for the MVP pilot

Status: accepted for MVP pilot setup.
Date: 2026-09-24.
Owner: architect/developer under delegated implementation authority.

The pilot may create an owner-scoped recipe through a trusted local
`recipe-create` command using explicitly supplied per-100-g nutrition. Optional
ingredient and instruction fields are retained as user-entered snapshots. An
ingredient without a catalog source is recorded as unresolved provenance; the
operator command does not infer nutrition from its name and does not call the
LLM or an external food database.

This provides a reproducible catalog fixture for testing saved-recipe
consumption in Telegram while preserving the existing backend calculation and
recipe-version pinning rules. User-facing recipe editing, natural-language
recipe definition, product lookup, and external comparison remain later work.

Related work: [W022](../work/022-local-recipe-provisioning.md), [W011](../work/011-recipe-persistence.md), [W012](../work/012-recipe-consumption.md), and [W020](../work/020-telegram-processing-loop.md).
