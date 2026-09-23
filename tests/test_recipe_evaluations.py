"""Recipe calculation fixtures and comparison checks."""

from decimal import Decimal
import json
from pathlib import Path
import unittest

from nutrition_contracts.common import NutrientValue, NutritionSnapshot
from nutrition_app.nutrition import recipe_per_100_g


FIXTURE = Path(__file__).parents[1] / "evals" / "fixtures" / "recipe_oatmeal_sum_yield_v1.json"


class RecipeEvaluationTests(unittest.TestCase):
    def test_oatmeal_sum_yield_matches_expected_and_general_reference(self):
        data = json.loads(FIXTURE.read_text())
        ingredients = []
        for item in data["ingredients"]:
            nutrition = NutritionSnapshot(**{
                name: NutrientValue(value=item["nutrition_per_100_g"][name], lower=None, upper=None)
                for name in ("kcal", "protein_g", "fat_g", "carbs_g")})
            ingredients.append((nutrition, Decimal(item["amount_g"])))
        result = recipe_per_100_g(ingredients, Decimal(data["yield"]["finished_yield_g"]))
        for name, expected in data["expected"]["per_100_g"].items():
            self.assertEqual(getattr(result, name).value, expected)
        total_kcal = Decimal(result.kcal.value) * Decimal(data["yield"]["finished_yield_g"]) / Decimal("100")
        self.assertAlmostEqual(total_kcal, Decimal(data["expected"]["total"]["kcal"]), places=5)
        self.assertLess(abs(total_kcal - Decimal(data["comparison"]["reference_total_kcal"])), Decimal("3"))
        self.assertGreater(Decimal(result.kcal.value), Decimal(data["comparison"]["close_prepared_product"]["kcal_per_100_g"]))


if __name__ == "__main__":
    unittest.main()
