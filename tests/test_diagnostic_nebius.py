import json
import unittest

from evals.diagnostic_nebius import DiagnosticNebiusParser
from nutrition_app.interpretation import ParserRequest
from nutrition_app.nebius import NebiusConfig


class DiagnosticNebiusTests(unittest.TestCase):
    def test_no_evidence_schema_is_eval_only_and_backend_derives_fixture(self):
        source = "Добавь шоколад 85% 10 гр"
        request = ParserRequest(
            source, "2026-09-22", "Europe/Berlin", ({
                "ref": "c1", "name": "шоколад тёмный 85%",
                "nutrition_basis": "per_100_g", "weight_basis": "as_sold",
                "food_kind": "general", "declared_fat_percent": None,
            },))
        output = {
            "schema_version": "1.0",
            "actions": [{
                "action_id": "a1", "depends_on": [], "unresolved": [],
                "kind": "add_food",
                "food": {"kind": "candidate", "candidate_ref": "c1", "candidate_kind": "product"},
                "quantity": {"amount": "10", "unit": "g"},
                "weight_basis": "as_sold", "date_hint": {"text": None}, "meal": "unspecified",
            }],
        }
        response = {"choices": [{"index": 0, "finish_reason": "stop", "message": {
            "role": "assistant", "content": json.dumps(output, ensure_ascii=False), "refusal": None,
        }}]}
        parser = DiagnosticNebiusParser(
            NebiusConfig("test-secret", "example/model"),
            request=lambda body, timeout: (200, {}, json.dumps(response).encode()),
        )

        parsed = json.loads(parser.parse(request))
        self.assertEqual(parsed["actions"][0]["evidence"], source)
        self.assertEqual(parsed["actions"][0]["quantity"]["amount"], "10")
        self.assertEqual(parsed["actions"][0]["food"]["candidate_ref"], "c1")
        self.assertNotIn("evidence", parser._schema["$defs"]["AddFood"]["properties"])
        self.assertEqual(parser._response_format["json_schema"]["name"],
                         "nutrition_parser_diagnostic_no_evidence")


if __name__ == "__main__":
    unittest.main()
