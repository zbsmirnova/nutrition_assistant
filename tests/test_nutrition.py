"""Arithmetic expectations calculated independently of the implementation helpers."""

from decimal import Decimal
import unittest

from nutrition_contracts.common import NutrientValue, NutritionSnapshot
from nutrition_app.errors import ApplicationError, NumericOverflow
from nutrition_app.nutrition import day_nutrition, decimal_text, entry_nutrition, recipe_per_100_g, scale


def snapshot(kcal="100", protein="4", fat="4", carbs="12"):
    return NutritionSnapshot(**{
        key: None if amount is None else NutrientValue(value=amount, lower=None, upper=None)
        for key, amount in zip(("kcal", "protein_g", "fat_g", "carbs_g"), (kcal, protein, fat, carbs))})


class NutritionTests(unittest.TestCase):
    def test_scales_each_nutrient_by_consumed_amount(self):
        result = scale(snapshot(), Decimal("250"))
        self.assertEqual([result.kcal.value, result.protein_g.value, result.fat_g.value, result.carbs_g.value],
                         ["250", "10", "10", "30"])

    def test_round_half_up_and_canonical_wire_values(self):
        self.assertEqual(decimal_text(Decimal("0.0000005")), "0.000001")
        self.assertEqual(decimal_text(Decimal("0.0000004999999")), "0")
        self.assertEqual(decimal_text(Decimal("10.100000")), "10.1")
        self.assertEqual(decimal_text(Decimal("100")), "100")

    def test_bounds_scale_without_inventing_missing_bounds(self):
        source = snapshot()
        source.kcal = NutrientValue(value="100", lower="80", upper="120")
        result = scale(source, Decimal("250"))
        self.assertEqual(result.kcal.model_dump(), {"value": "250", "lower": "200", "upper": "300"})
        self.assertIsNone(result.protein_g.lower)

    def test_partial_wholly_unknown_empty_and_known_zero_differ(self):
        partial = day_nutrition([snapshot(fat=None), snapshot(fat="0")])
        self.assertEqual(partial.fat_g.model_dump(), {
            "kind": "partial", "known_subtotal": "0", "known_components": 1, "unknown_components": 1})
        self.assertEqual(day_nutrition([snapshot(fat=None)]).fat_g.kind, "unknown")
        self.assertEqual(day_nutrition([]).fat_g.kind, "empty")
        known_zero = day_nutrition([snapshot(fat="0")]).fat_g
        self.assertEqual(known_zero.kind, "complete")
        self.assertEqual(known_zero.amount.value, "0")

    def test_entry_does_not_present_partial_nutrient_as_complete(self):
        result = entry_nutrition([snapshot(), snapshot(fat=None)])
        self.assertIsNone(result.fat_g)
        self.assertEqual(result.kcal.value, "200")

    def test_aggregate_bounds_only_when_every_known_component_has_bounds(self):
        bounded = snapshot()
        bounded.kcal = NutrientValue(value="100", lower="80", upper="120")
        all_bounded = day_nutrition([bounded, bounded]).kcal.amount
        self.assertEqual(all_bounded.model_dump(), {"value": "200", "lower": "160", "upper": "240"})
        self.assertIsNone(day_nutrition([bounded, snapshot()]).kcal.amount.lower)

    def test_invalid_and_overflow_values_are_rejected(self):
        for value in ("NaN", "Infinity", "-0.1", "1000000000000", "999999999999.9999991"):
            with self.subTest(value=value), self.assertRaises(NumericOverflow):
                decimal_text(Decimal(value))
        for value in ("0", "-1", "NaN"):
            with self.subTest(value=value), self.assertRaises(ApplicationError):
                scale(snapshot(), Decimal(value))

    def test_scaling_and_day_aggregation_check_overflow(self):
        maximum = snapshot(kcal="999999999999.999999")
        with self.assertRaises(NumericOverflow):
            scale(maximum, Decimal("200"))
        with self.assertRaises(NumericOverflow):
            day_nutrition([maximum, maximum])

    def test_recipe_sum_yield_matches_oatmeal_expectation_and_general_reference(self):
        oats = snapshot(kcal="376", protein="13.2", fat="6.5", carbs="67.7")
        sugar = snapshot(kcal="400", protein="0", fat="0", carbs="100")
        water = snapshot(kcal="0", protein="0", fat="0", carbs="0")
        result = recipe_per_100_g([
            (oats, Decimal("93")), (sugar, Decimal("2")), (water, Decimal("375"))], Decimal("470"))
        self.assertEqual(result.kcal.value, "76.102128")
        self.assertEqual(result.protein_g.value, "2.611915")
        self.assertEqual(result.fat_g.value, "1.28617")
        self.assertEqual(result.carbs_g.value, "13.821489")
        total_kcal = Decimal(result.kcal.value) * Decimal("470") / Decimal("100")
        self.assertAlmostEqual(total_kcal, Decimal("357.68"), places=5)
        # USDA close references: dry oats 379 kcal/100 g and granulated sugar
        # 387 kcal/100 g produce 360.21 kcal for the same normalized inputs.
        reference_total = Decimal("93") * Decimal("379") / Decimal("100") + Decimal("2") * Decimal("387") / Decimal("100")
        self.assertLess(abs(total_kcal - reference_total), Decimal("3"))

    def test_recipe_per_100_g_keeps_unknown_nutrients_unknown(self):
        result = recipe_per_100_g([
            (snapshot(fat=None), Decimal("100")),
            (snapshot(), Decimal("100")),
        ], Decimal("200"))
        self.assertIsNone(result.fat_g)
        self.assertEqual(result.kcal.value, "100")

    def test_recipe_per_100_g_rejects_empty_or_invalid_yield(self):
        source = [(snapshot(), Decimal("100"))]
        with self.assertRaises(ApplicationError):
            recipe_per_100_g([], Decimal("100"))
        for yield_g in (Decimal("0"), Decimal("-1")):
            with self.subTest(yield_g=yield_g), self.assertRaises(ApplicationError):
                recipe_per_100_g(source, yield_g)

    def test_recipe_keeps_full_precision_until_final_output(self):
        source = snapshot(kcal="1.234567")
        result = recipe_per_100_g([(source, Decimal("25"))], Decimal("25"))
        self.assertEqual(result.kcal.value, "1.234567")
        bounded = source.model_copy(update={
            "kcal": NutrientValue(value="1", lower="0.999999", upper="1.000001")})
        result = recipe_per_100_g([(bounded, Decimal("0.000001"))], Decimal("0.000001"))
        self.assertEqual(result.kcal.model_dump(), {
            "value": "1", "lower": "0.999999", "upper": "1.000001"})

    def test_persisted_component_rounding_is_used_for_day_totals(self):
        small = snapshot(kcal="0.000001")
        a = scale(small, Decimal("50"))
        b = scale(small, Decimal("50"))
        self.assertEqual(a.kcal.value, "0.000001")
        self.assertEqual(day_nutrition([a, b]).kcal.amount.value, "0.000002")
