"""Integrity checks for the authored real-life evaluation corpus, not model scoring."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


CORPUS = Path(__file__).parents[1] / "evals" / "real_life_v1.json"


class RealLifeEvalCorpusTests(unittest.TestCase):
    def test_corpus_has_stable_complete_case_ids_and_required_expectations(self) -> None:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cases = corpus["cases"]

        self.assertEqual(corpus["format_version"], "1.0")
        self.assertEqual([case["id"] for case in cases], [f"RL-{number:03d}" for number in range(1, 51)])
        self.assertEqual(len(cases), 50)

        for case in cases:
            self.assertTrue(case["category"])
            self.assertTrue(case["message"])
            self.assertIn(case["scope"], {"future_v1", "v2"})
            self.assertTrue(case["expect"]["intent"])
            self.assertTrue(case["expect"]["effects"])
            self.assertTrue(case["expect"]["invariants"])

    def test_declared_dependencies_refer_to_earlier_cases(self) -> None:
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        seen: set[str] = set()
        for case in cases:
            for dependency in case.get("depends_on", []):
                self.assertIn(dependency, seen)
            seen.add(case["id"])
