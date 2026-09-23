"""Structural checks for user-authored recipe-calculation evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


CORPUS = Path(__file__).parents[1] / "evals" / "recipe_calculation_v1.json"


class RecipeCalculationEvalTests(unittest.TestCase):
    def test_recipe_calculation_cases_have_yield_and_non_consumption_guards(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cases = corpus["cases"]

        self.assertEqual(corpus["format_version"], "1.0")
        self.assertEqual([case["id"] for case in cases], [f"RECIPE-CALC-{number:03d}" for number in range(1, 4)])
        for case in cases:
            self.assertEqual(case["expect"]["intent"], "recipe_calculation")
            self.assertTrue(case["expect"]["initial_ingredients"])
            self.assertTrue(case["expect"]["provisional_yield_g"])
            self.assertIn("log the", " ".join(case["expect"]["must_not"]))
