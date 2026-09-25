# D045 — Post-MVP restaurant calorie estimation range

Kind: product.
Status: accepted for post-MVP planning.
Recorded: 2026-09-24.
Decision owner: product owner.
Acceptance evidence: explicit product direction in the discussion.
Related questions: validate the reference database, similarity rules, and range quality during the post-MVP slice.

## Context

Restaurant meals often have hidden oils, dressings, sauces, and larger cooking
fat quantities than a home preparation. Requiring exact weighing is usually
uncomfortable and can cause the user to skip logging. The hybrid tracking
principle therefore needs a useful estimate path for unfamiliar restaurant
food.

## Decision

After MVP, when the assistant cannot identify an exact restaurant dish, it may
search an approved reference database for similar foods and calculate a
baseline calorie estimate from the matching references. The first proposed
range is:

```text
lower bound = reference average
upper bound = reference average × 1.30
```

The upper margin represents a working hypothesis about hidden restaurant fats
and must be tested against examples before being treated as an accuracy claim.
The assistant should explain that this is an estimate, show the reference
basis and portion assumption, and ask the user to approve the range or select a
different interpretation. It must not add the meal to totals from the model or
provider suggestion alone.

The saved record must retain the selected reference sources, portion, range,
user decision, and estimate provenance. A later personal confirmation may add
the selected interpretation to the user's local cache without changing the
historical restaurant entry silently.

## Boundaries and validation

This is a post-MVP behavior. It requires an approved provider or licensed
dataset, similarity and regional matching, duplicate/outlier handling, and
evaluation on real restaurant-style examples. The 30% margin is a product
hypothesis, not a nutritional fact. The flow must remain optional and
nonjudgmental, and it must preserve the user's ability to log a rough meal
without pretending that its calories are exact.

## References

See [user-guide-v1.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/user-guide-v1.md?type=file&root=%252F), [0044-hybrid-tracking-principles.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/decisions/0044-hybrid-tracking-principles.md?type=file&root=%252F), and [026-restaurant-calorie-estimation.md](air-file://fai6b8iclscp0tss0s3r/Users/Zinaida.Smirnova/air/nutrition_assistant/docs/work/026-restaurant-calorie-estimation.md?type=file&root=%252F).
