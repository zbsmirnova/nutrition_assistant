# D044 — Hybrid tracking principles

Kind: product.
Status: accepted for MVP onboarding and pilot UX.
Recorded: 2026-09-24.
Decision owner: product owner.
Acceptance evidence: explicit user acceptance in the product discussion.
Related questions: none.

## Context

Requiring exact weighing for every meal would add friction and make sustained
tracking harder. The product should teach useful portion awareness at home and
support practical estimates in social settings, while preserving honest
uncertainty and focusing precision where it changes nutrition totals most.

## Decision

Expected user behavior is hybrid tracking:

1. During the first phase, weigh food at home often enough to learn visual
   references for recurring portions, especially for calorie-dense ingredients.
2. In restaurants and at other people's homes, the user may make a reasonable
   estimate when weighing is uncomfortable. An estimate is preferable to
   omitting the meal, but it must remain visibly approximate and carry any
   available uncertainty.
3. As confidence grows, the user may reuse stable personal references for
   recurring portions, such as a usual apple or a habitual teaspoon of oil.
4. Precision should focus on oils, sauces, dressings, spreads, and other
   calorie-dense foods. Low-calorie vegetables without dressing usually do not
   need the same measurement effort.

The assistant must not present an estimate as a measured value. The personal
product cache and recurring portion references should make this workflow faster
over time.

## Consequences and limits

This principle supports sustainable logging and the 20/80 approach. It does not
authorize the model to invent nutrition, silently choose among products, or
turn unknown restaurant nutrition into an exact value. Current MVP behavior
still requires an explicit approved estimate where that path is implemented;
restaurant nutrition remains a future behavior to validate separately.

## References

See [user-guide-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/user-guide-v1.md?type=file&root=%252F) and the enduring `HYBRID-001` requirement in [CONSTITUTION.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/CONSTITUTION.md?type=file&root=%252F).
