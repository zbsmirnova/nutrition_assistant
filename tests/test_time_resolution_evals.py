"""Structural checks for user-authored time-resolution evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


CORPUS = Path(__file__).parents[1] / "evals" / "time_resolution_v1.json"


class TimeResolutionEvalTests(unittest.TestCase):
    def test_cases_have_stable_date_expectations(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cases = corpus["cases"]

        self.assertEqual(corpus["format_version"], "1.0")
        self.assertEqual([case["id"] for case in cases], [f"TIME-{number:03d}" for number in range(1, 5)])
        self.assertEqual(corpus["shared_fixture"]["time_zone"], "Europe/Berlin")
        for case in cases:
            self.assertTrue(case["message"])
            self.assertIn("model_date_hint", case["expect"])
            self.assertTrue(case["expect"].get("backend_effective_date") or case["expect"].get("backend_disposition"))
