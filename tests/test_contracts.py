"""Contract validation and authored examples, not live-model or database tests."""

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError

from nutrition_contracts.commands import CommandEnvelope
from nutrition_contracts.common import Mass, NutrientValue, PositiveDecimal
from nutrition_contracts.export import SCHEMA_DIRECTORY, SCHEMA_MODELS, schema_for
from nutrition_contracts.parser import ParserOutput, validate_parser_context
from nutrition_contracts.results import OutcomeEnvelope
from pydantic import TypeAdapter


EXAMPLES = SCHEMA_DIRECTORY / "examples"


def example(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text())


def wire(model, value):
    return model.model_validate_json(json.dumps(value, ensure_ascii=False))


def check_context(fixture, output=None):
    validate_parser_context(
        output or wire(ParserOutput, fixture["parser"]),
        fixture["context"]["candidates"], fixture["context"]["pending_questions"],
        source_text=fixture["source"]["text"], has_reply=fixture["context"]["has_reply"],
    )


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = {
            name: Draft202012Validator(schema_for(name), format_checker=FormatChecker())
            for name in SCHEMA_MODELS
        }

    def assert_structurally_invalid(self, kind, payload):
        with self.assertRaises(ValidationError):
            wire(SCHEMA_MODELS[kind], payload)
        self.assertFalse(self.validators[kind].is_valid(payload), "portable schema must reject this too")

    def test_schema_exports_are_current_and_valid(self):
        for name in SCHEMA_MODELS:
            with self.subTest(schema=name):
                generated = schema_for(name)
                Draft202012Validator.check_schema(generated)
                self.assertEqual(json.loads((SCHEMA_DIRECTORY / f"{name}.schema.json").read_text()), generated)

    def test_every_exported_object_is_closed(self):
        def visit(value):
            if isinstance(value, dict):
                if value.get("type") == "object":
                    self.assertIs(value.get("additionalProperties"), False)
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/$defs/"), "validation must not fetch remote schemas")
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        for name in SCHEMA_MODELS:
            visit(schema_for(name))

    def test_all_authored_scenarios_validate_with_both_validators(self):
        paths = sorted(EXAMPLES.glob("[0-9][0-9]_*.json"))
        self.assertEqual(len(paths), 20)
        for path in paths:
            data = json.loads(path.read_text())
            with self.subTest(scenario=path.stem, layer="parser"):
                self.validators["parser-output"].validate(data["parser"])
                parsed = wire(ParserOutput, data["parser"])
                check_context(data, parsed)
                self.assertEqual(parsed.model_dump(mode="json"), data["parser"])
            for name, values in (("command", data["commands"]), ("outcome", data["results"])):
                for index, value in enumerate(values):
                    with self.subTest(scenario=path.stem, layer=name, index=index):
                        self.validators[name].validate(value)
                        instance = wire(SCHEMA_MODELS[name], value)
                        self.assertEqual(instance.model_dump(mode="json"), value)

    def test_parser_cannot_supply_authorization_or_calculated_nutrition(self):
        for path, field, value in (
            ([], "user_id", "00000000-0000-4000-8000-000000000001"),
            (["actions", 0], "calculated_kcal", "175"),
            (["actions", 0, "food"], "recipe_version_id", "00000000-0000-4000-8000-000000000101"),
        ):
            data = example("01_add_food")["parser"]
            target = data
            for key in path:
                target = target[key]
            target[field] = value
            with self.subTest(field=field):
                self.assert_structurally_invalid("parser-output", data)

    def test_command_envelope_is_not_a_parser_output(self):
        self.assert_structurally_invalid("parser-output", example("01_add_food")["commands"][0])

    def test_decimal_amounts_are_positive_canonical_strings(self):
        invalid = [0, 1.2, True, "0", "0.000000", "-1", "1,2", "1e2", "NaN", "Infinity", "01", ".5", "1.", " 1", "1 ", "1\n", "0.0000001"]
        for amount in invalid:
            with self.subTest(amount=repr(amount)):
                data = example("01_add_food")["parser"]
                data["actions"][0]["quantity"]["amount"] = amount
                self.assert_structurally_invalid("parser-output", data)
        adapter = TypeAdapter(PositiveDecimal)
        for amount in ("1", "0.1", "0.000001", "100.000000", "999999999999.999999"):
            self.assertEqual(adapter.validate_json(json.dumps(amount)), amount)

    def test_missing_parser_quantity_is_allowed_but_unresolved_command_is_not(self):
        data = example("02_mixed_food")
        wire(ParserOutput, data["parser"])
        cmd = data["commands"][0]
        cmd["command"]["food"]["components"][0]["eaten_grams"] = None
        self.assert_structurally_invalid("command", cmd)

    def test_step_counts_are_strict_integers_with_correct_zero_policy(self):
        for value in (True, "9000", -1, 1.5):
            cmd = example("06_same_daily_steps")["commands"][0]
            cmd["command"]["steps"] = value
            with self.subTest(value=value):
                self.assert_structurally_invalid("command", cmd)
        cmd["command"]["steps"] = 0
        wire(CommandEnvelope, cmd)
        cmd = example("07_increment_daily_steps")["commands"][0]
        cmd["command"]["steps"] = 0
        self.assert_structurally_invalid("command", cmd)

    def test_revision_guards_are_required_for_corrections_and_increments(self):
        for name in ("04_correct_food", "07_increment_daily_steps"):
            data = example(name)["commands"][0]
            del data["command"]["expected_revision_id"]
            with self.subTest(scenario=name):
                self.assert_structurally_invalid("command", data)

    def test_whole_floats_still_require_strict_python_validation(self):
        # JSON Schema defines integer mathematically, whereas the wire model
        # deliberately requires a JSON integer token for step counts.
        data = example("06_same_daily_steps")["commands"][0]
        data["command"]["steps"] = 9000.0
        self.assertTrue(self.validators["command"].is_valid(data))
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)

    def test_dates_and_ids_are_validated(self):
        for field, value in (("effective_date", "2026-02-30"), ("effective_date", "yesterday"), ("expected_revision_id", "made-up")):
            data = example("05_replace_daily_weight")["commands"][0]
            data["command"][field] = value
            with self.subTest(field=field, value=value):
                self.assert_structurally_invalid("command", data)

    def test_time_zone_validation_is_a_python_semantic_check(self):
        data = example("05_replace_daily_weight")["commands"][0]
        data["command"]["time_zone"] = "Invented/Zone"
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)

    def test_recipe_has_no_default_portion_or_batch_fields(self):
        for field in ("default_portion_g", "servings_count", "batch_id"):
            data = example("09_recipe_calculation_answer")["commands"][0]
            data["command"]["recipe"][field] = 250
            with self.subTest(field=field):
                self.assert_structurally_invalid("command", data)

    def test_calculated_recipe_accepts_inputs_not_model_computed_output(self):
        data = example("09_recipe_calculation_answer")["commands"][0]
        data["command"]["recipe"]["nutrition"]["per_100_g"] = {}
        self.assert_structurally_invalid("command", data)
        parser = example("08_recipe_needs_finished_weight")["parser"]
        parser["actions"][0]["nutrition_input"]["per_100_g"] = {}
        self.assert_structurally_invalid("parser-output", parser)

    def test_recipe_consumption_requires_grams_not_a_stored_serving(self):
        data = example("01_add_food")["commands"][0]
        component = data["command"]["food"]["components"][0]
        del component["eaten_grams"]
        component["servings"] = 1
        self.assert_structurally_invalid("command", data)

    def test_recipe_calculation_requires_ingredients_and_positive_yield(self):
        data = example("09_recipe_calculation_answer")["commands"][0]
        data["command"]["recipe"]["nutrition"]["finished_yield_g"] = "0"
        self.assert_structurally_invalid("command", data)
        data = example("09_recipe_calculation_answer")["commands"][0]
        data["command"]["recipe"]["ingredients"] = []
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)

    def test_estimated_yield_requires_approval_in_source_chain(self):
        data = example("09_recipe_calculation_answer")["commands"][0]
        calculation = data["command"]["recipe"]["nutrition"]
        calculation["yield_basis"] = "user_confirmed_estimate"
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)
        calculation["estimate_approval_update_id"] = "00000000-0000-4000-8000-999999999999"
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)
        calculation["estimate_approval_update_id"] = data["source"]["evidence_update_ids"][-1]
        wire(CommandEnvelope, data)  # The backend must additionally verify actual consent in that message.

    def test_ingredient_sum_yield_needs_no_cooked_weight_approval(self):
        data = example("09_recipe_calculation_answer")["commands"][0]
        calculation = data["command"]["recipe"]["nutrition"]
        calculation["yield_basis"] = "ingredient_sum_no_evaporation"
        calculation["estimate_approval_update_id"] = None
        wire(CommandEnvelope, data)

    def test_original_update_is_required_in_evidence(self):
        data = example("03_clarification_after_midnight")["commands"][0]
        data["source"]["evidence_update_ids"] = data["source"]["evidence_update_ids"][1:]
        with self.assertRaises(ValidationError):
            wire(CommandEnvelope, data)

    def test_candidate_context_rejects_invented_and_wrong_kind_refs(self):
        data = example("01_add_food")
        data["parser"]["actions"][0]["food"]["candidate_ref"] = "c999"
        with self.assertRaises(ValueError):
            check_context(data)
        data = example("01_add_food")
        data["context"]["candidates"]["c1"] = "product"
        with self.assertRaises(ValueError):
            check_context(data)

    def test_reply_target_requires_actual_reply_context(self):
        data = example("04_correct_food")
        data["context"]["has_reply"] = False
        with self.assertRaises(ValueError):
            check_context(data)

    def test_evidence_must_come_from_source(self):
        data = example("01_add_food")
        data["parser"]["actions"][0]["evidence"] = "I ate three cakes"
        with self.assertRaises(ValueError):
            check_context(data)

    def test_source_action_evidence_is_nontrivial_but_short_replies_are_allowed(self):
        data = example("01_add_food")
        data["parser"]["actions"][0]["evidence"] = "я"
        with self.assertRaises(ValidationError):
            wire(ParserOutput, data["parser"])
        reply = example("03_clarification_after_midnight")
        reply["parser"]["actions"][0]["evidence"] = "5%"
        wire(ParserOutput, reply["parser"])

    def test_action_ids_dependencies_and_recipe_result_references(self):
        for defect in ("duplicate_id", "missing_dependency", "cycle", "undeclared_result", "wrong_result_type"):
            data = example("11_define_recipe_then_eat")["parser"]
            first, second = data["actions"]
            if defect == "duplicate_id":
                second["action_id"] = first["action_id"]
            elif defect == "missing_dependency":
                second["depends_on"] = ["a999"]
            elif defect == "cycle":
                first["depends_on"] = ["a2"]
            elif defect == "undeclared_result":
                second["depends_on"] = []
            else:
                data["actions"][0] = {k: first[k] for k in ("action_id", "evidence", "depends_on", "unresolved")}
                data["actions"][0].update(kind="non_logging", reason="planned_food")
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                wire(ParserOutput, data)

    def test_clarification_checks_question_identity_and_answer_type(self):
        for defect in ("unknown_question", "wrong_type", "duplicate_question"):
            data = example("03_clarification_after_midnight")
            answers = data["parser"]["actions"][0]["answers"]
            if defect == "unknown_question":
                answers[0]["question_ref"] = "q999"
            elif defect == "wrong_type":
                answers[0]["value"] = {"kind":"text", "text":"forty"}
            else:
                answers.append(deepcopy(answers[0]))
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                check_context(data)

    def test_nutrient_ranges_are_paired_and_ordered(self):
        for raw in ({"value":"10","lower":"12","upper":"20"}, {"value":"10","lower":"5","upper":None}):
            with self.assertRaises(ValidationError):
                wire(NutrientValue, raw)

    def test_bone_weights_remain_physically_consistent(self):
        data = example("17_bones_correction")["commands"][0]["command"]["replacement"]["components"][0]["quantity"]
        data["edible_g"] = "200"
        with self.assertRaises(ValidationError):
            wire(Mass, data)

    def test_food_outcome_requires_entry_and_daily_summary(self):
        data = example("01_add_food")["results"][0]
        data["result"]["daily_summaries"] = []
        with self.assertRaises(ValidationError):
            wire(OutcomeEnvelope, data)
        data = example("01_add_food")["results"][0]
        data["result"]["food_entries"] = []
        with self.assertRaises(ValidationError):
            wire(OutcomeEnvelope, data)

    def test_summary_coverage_and_observation_receipts_match(self):
        data = example("15_late_food_unknown_nutrient")["results"][0]
        data["result"]["daily_summaries"][0]["nutrition"]["fat_g"]["known_components"] = 2
        with self.assertRaises(ValidationError):
            wire(OutcomeEnvelope, data)
        data = example("05_replace_daily_weight")["results"][0]
        data["result"]["observations"][0]["revision_id"] = "00000000-0000-4000-8000-999999999999"
        with self.assertRaises(ValidationError):
            wire(OutcomeEnvelope, data)

    def test_partial_example_reuses_operation_and_keeps_original_date(self):
        first, reply = example("02_mixed_food"), example("03_clarification_after_midnight")
        pending = first["results"][1]["result"]
        command = reply["commands"][0]
        self.assertEqual(command["operation_id"], pending["operation_id"])
        self.assertEqual(command["source"]["pending_action_id"], pending["pending_action_id"])
        self.assertEqual(command["source"]["origin_update_id"], first["commands"][0]["source"]["origin_update_id"])
        self.assertNotEqual(reply["source"]["local_date"], command["command"]["food"]["effective_date"])
        self.assertEqual(command["command"]["food"]["effective_date"], first["source"]["local_date"])
        self.assertEqual(len(reply["commands"]), 1)
        self.assertEqual(command["command"]["food"]["components"][0]["kind"], "product")

    def test_scenarios_distinguish_food_catalog_questions_and_plans(self):
        self.assertEqual(example("12_planned_food")["commands"], [])
        self.assertEqual(example("13_food_question")["commands"][0]["command"]["kind"], "preview_food")
        self.assertEqual(example("10_recipe_direct_input")["commands"][0]["command"]["kind"], "define_recipe")
        self.assertEqual(example("10_recipe_direct_input")["results"][0]["result"]["food_entries"], [])
        self.assertEqual(example("18_weight_while_food_pending")["parser"]["actions"][0]["kind"], "set_daily_weight")

    def test_late_addition_stays_complete_and_missing_nutrient_is_not_zero(self):
        result = example("15_late_food_unknown_nutrient")["results"][0]["result"]
        self.assertIsNone(result["food_entries"][0]["nutrition"]["fat_g"])
        self.assertEqual(result["daily_summaries"][0]["completeness"], "complete")
        self.assertEqual(result["daily_summaries"][0]["nutrition"]["fat_g"]["kind"], "partial")

    def test_recipe_fixture_preserves_input_amounts_and_calculates_per_100_g(self):
        start = example("08_recipe_needs_finished_weight")
        end = example("09_recipe_calculation_answer")
        cmd = end["commands"][0]["command"]["recipe"]
        result = end["results"][0]["result"]["recipe"]
        self.assertEqual(end["commands"][0]["operation_id"], start["results"][0]["result"]["operation_id"])
        self.assertEqual(result["ingredients"], cmd["ingredients"])
        self.assertEqual(result["cooking_instructions"], "Варить 30 минут.")
        self.assertEqual([i["original_quantity"]["amount"] for i in result["ingredients"]], ["300","120","250","800"])
        catalog = json.loads((EXAMPLES / "catalog.json").read_text())["per_100_g"]
        for nutrient in ("kcal", "protein_g", "fat_g", "carbs_g"):
            total = sum(Decimal(catalog[i["source"]["product_version_id"]][nutrient]["value"]) * Decimal(i["source"]["quantity"]["edible_g"]) / 100 for i in cmd["ingredients"])
            per_100 = (total * 100 / Decimal(cmd["nutrition"]["finished_yield_g"])).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            self.assertEqual(per_100, Decimal(result["per_100_g"][nutrient]["value"]))

    def test_food_fixture_arithmetic_uses_pinned_source_versions(self):
        catalog = json.loads((EXAMPLES / "catalog.json").read_text())["per_100_g"]
        for name in ("01_add_food", "04_correct_food", "17_bones_correction"):
            data = example(name)
            command = data["commands"][0]["command"]
            component = command.get("food", command.get("replacement"))["components"][0]
            version_id = component.get("recipe_version_id", component.get("product_version_id"))
            grams = component.get("eaten_grams") or component["quantity"]["edible_g"]
            result = data["results"][0]["result"]["food_entries"][0]["nutrition"]
            for nutrient in ("kcal", "protein_g", "fat_g", "carbs_g"):
                self.assertEqual(Decimal(result[nutrient]["value"]), Decimal(catalog[version_id][nutrient]["value"]) * Decimal(grams) / 100)


if __name__ == "__main__":
    unittest.main()
