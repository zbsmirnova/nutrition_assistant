"""Structural checks for user-authored intake evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


CORPUS = Path(__file__).parents[1] / "evals" / "intake_v1.json"


class IntakeEvalTests(unittest.TestCase):
    def test_cases_have_stable_ids_and_evaluable_context(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cases = corpus["cases"]

        self.assertEqual(corpus["format_version"], "1.0")
        self.assertEqual([case["id"] for case in cases], [f"INTAKE-{number:03d}" for number in range(1, 10)])
        for case in cases:
            self.assertTrue(case["turns"])
            self.assertTrue(case["fixtures"])
            self.assertTrue(case["expect"]["intent"])
            self.assertTrue(case["expect"].get("calculation") or case["expect"].get("clarifications"))

    def test_fixture_contract_requires_independent_numeric_oracle(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.assertIn("numeric_oracle", corpus["fixture_contract"])
