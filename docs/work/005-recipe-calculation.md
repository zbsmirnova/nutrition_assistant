# Work brief 005 — Recipe calculation foundation

Status: done for the calculation foundation; M3 remains in progress.
Updated: 2026-09-23.
Depends on: M1 arithmetic and typed contracts.
Decision: D014.

## Goal

Make ingredient-based recipe arithmetic deterministic before adding recipe persistence or conversational recipe resumption. The first fixture is oatmeal made from 93 g oats, approximately 2 g sugar, and 375 ml water.

## Accepted behavior

- Normalize volume ingredients to mass through a pinned source density before summing them. The oatmeal fixture uses water at 1 g/ml, so the conditional yield is about 470 g.
- Calculate each nutrient from the ingredient source snapshot, then divide the total by the chosen yield and multiply by 100.
- Record `ingredient_sum_no_evaporation` as provenance when the sum is used. It is not a serving size and does not claim a measured cooked weight.
- Keep unknown source nutrients unknown. The LLM does not perform arithmetic.
- Use measured or user-confirmed estimated yield when the cooking process includes loss-sensitive instructions or when a source mass cannot be normalized safely.
- Save original ingredient quantities and units in the eventual recipe version; this work does not yet add recipe database tables or recipe consumption.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| W005-A01 | Typed commands accept `ingredient_sum_no_evaporation` and still require approval for `user_confirmed_estimate`. |
| W005-A02 | Backend recipe arithmetic calculates the oatmeal fixture as 357.68 kcal total and 76.102128 kcal/100 g from the selected catalog snapshot. |
| W005-A03 | Unknown nutrient components remain unknown in the calculated recipe profile. |
| W005-A04 | The fixture compares within 3 kcal of the same dry-ingredient calculation using USDA FoodData Central references and explains why prepared oatmeal is a different comparison. |
| W005-A05 | Recipe component sums retain full Decimal precision until final persisted output, including nutrient bounds. |
| W005-A06 | Generated schemas, contract tests, arithmetic tests, and the source-specific recipe evaluation pass. |

## Not in this slice

Recipe CRUD, database migrations, catalog search, natural-language ingredient resolution, cooking-loss classification, recipe clarification/resumption, recipe consumption, and Telegram rendering remain subsequent work. The USDA comparison is a validation reference, not a runtime provider dependency.
