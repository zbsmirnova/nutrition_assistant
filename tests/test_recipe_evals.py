"""Structural checks for user-authored recipe evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


CORPUS = Path(__file__).parents[1] / "evals" / "recipe_v1.json"


class RecipeEvalTests(unittest.TestCase):
    def test_recipe_recall_cases_cover_unique_and_ambiguous_matches(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cases = corpus["cases"]

        self.assertEqual(corpus["format_version"], "1.0")
        self.assertEqual([case["id"] for case in cases], ["RECIPE-001", "RECIPE-002"])
        self.assertIn("resolution", cases[0]["expect"])
        self.assertEqual(cases[1]["expect"]["disposition"], "needs_recipe_clarification")
