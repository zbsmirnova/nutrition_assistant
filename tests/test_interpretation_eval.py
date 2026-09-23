import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals import run_interpretation_eval


class InterpretationEvalRunnerTests(unittest.TestCase):
    def test_render_json_prints_saved_report_without_running_parser(self):
        report = {
            "parser": "stub:test",
            "prompt": "production (nebius_prompt.txt)",
            "thresholds": {
                "case_pass_rate": "0.70",
                "clarification_accuracy": "0.80",
                "quantity_extraction": "0.90",
            },
            "results": [{
                "id": "INTAKE-002",
                "known_gaps": 0,
                "checks": {"consumed": True},
                "passed": True,
                "n_add_food": 1,
                "clarification_raised": False,
            }],
            "summary": {
                "case_pass_rate": "1.00 (1)",
                "consumed": "1.00 (1)",
                "add_food_count": "1.00 (1)",
                "evidence_valid": "n/a",
                "date_hint_valid": "n/a",
                "clarification_recall": "n/a",
                "clarification_specificity": "n/a",
                "quantity_extraction": "n/a",
                "candidate_selection": "n/a",
                "max_add_food_respected": "n/a",
                "errors": 0,
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            output = StringIO()
            with patch.object(run_interpretation_eval, "run", side_effect=AssertionError("parser called")):
                with redirect_stdout(output):
                    result = run_interpretation_eval.main(["--render-json", str(path)])

        self.assertEqual(result, 0)
        rendered = output.getvalue()
        self.assertIn("Parser: stub:test", rendered)
        self.assertIn("INTAKE-002   yes", rendered)
        self.assertIn("case pass rate        1.00 (1)", rendered)

    def test_render_json_reports_missing_file(self):
        with self.assertRaises(SystemExit) as raised:
            run_interpretation_eval.main(["--render-json", "/tmp/does-not-exist-interp.json"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
