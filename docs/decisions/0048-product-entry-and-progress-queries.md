# D048 — Product entry completion and on-demand progress queries

Kind: product/technical.
Status: accepted for the catalog-growth slice after core MVP validation and for post-MVP reporting order.
Recorded: 2026-09-25.
Decision owner: product owner.
Acceptance evidence: explicit user acceptance of label-based product entry, manual completion after rejecting an analogue, and first-priority on-demand progress questions.
Related questions: Q04, Q08.

## Decision

The user may create a personal product through Telegram from typed label values.
Kcal and protein per 100 g are required. If fat and carbohydrates are absent,
the model may propose values from a nearest analogue and ask for confirmation.
If the user rejects the proposal, the bot asks for the two values manually. It
does not create a pending or incomplete active product, and missing values are
never silently converted to zero.

Future label-photo and barcode input are alternate ways to populate the same
versioned product profile; they are outside the MVP.

The first validation pass intentionally starts with products and recipes
provisioned through the trusted local commands. Telegram product creation is
the next slice after that gate, so the personal database can grow through
normal use without expanding the persistence experiment.

The first post-MVP reporting slice is on-demand, read-only progress questions
in ordinary Telegram language. The model classifies the question into a typed
report request, the backend calculates it from durable entries and observations,
and the model renders the result. Scheduled reports and reminders reuse this
report service later.

## Consequences and limits

Product creation adds one confirmation turn when the label omits fat or
carbohydrates, but prevents incomplete profiles from contaminating later
calculations. Read-only progress queries can be implemented without granting
the model direct database access and without waiting for scheduler work.

## References

See [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F), [conversation-contract-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/conversation-contract-v1.md?type=file&root=%252F), and [roadmap.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/roadmap.md?type=file&root=%252F).
