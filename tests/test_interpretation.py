"""W003 resolution expectations: controlled proposals, not live-model evaluation."""
from copy import deepcopy
import json
import unittest
from uuid import UUID

from nutrition_contracts.commands import GetDaySummary
from nutrition_contracts.parser import ParserOutput
from nutrition_app.conversation_demo import PRODUCT_NAME, TEXT, fixture
from nutrition_app.conversation import ConversationWorker
from nutrition_app.interpretation import (CONTEXT_VERSION, RESOLVER_VERSION, ParserUnavailable,
                                         SyntheticParser, parser_request, resolve)


ACTOR = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
ORIGIN = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
VERSION = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


def context(text=TEXT):
    return {"source_text": text, "local_date": "2026-09-22", "time_zone": "Europe/Berlin",
            "context_revision": 0, "context_version": CONTEXT_VERSION, "resolver_version": RESOLVER_VERSION,
            "schema_version": "1.0", "has_reply": False, "forwarded": False, "catalog_overflow": False,
            "observations": [],
            "candidates": [{"ref": "c1", "version_id": str(VERSION), "name": PRODUCT_NAME,
                "nutrition_basis": "per_100_g", "weight_basis": "as_sold", "food_kind": "dairy",
                "declared_fat_percent": "5.00"}]}


def proposal(text=TEXT, **changes):
    data = fixture(text)["output"]
    data["actions"][0].update(changes)
    return ParserOutput.model_validate_json(json.dumps(data))


def observation_proposal(kind, text, **fields):
    action = {"kind": kind, "action_id": "a1", "evidence": text,
              "depends_on": [], "unresolved": [], "date_hint": {"text": None}}
    action.update(fields)
    return ParserOutput.model_validate({"schema_version": "1.0", "actions": [action]})


class InterpretationTests(unittest.TestCase):
    def test_day_read_resolves_to_backend_owned_command(self):
        text = "Сколько калорий сегодня?"
        result = resolve(ACTOR, ORIGIN, context(text), ParserOutput.model_validate({
            "schema_version": "1.0", "actions": [{
                "kind": "get_day_summary", "action_id": "a1", "evidence": text,
                "depends_on": [], "unresolved": [], "date_hint": {"text": "сегодня"},
            }] }))
        self.assertEqual((result.status, result.reason), ("ready", "day_summary_command_prepared"))
        self.assertIsInstance(result.command.command, GetDaySummary)
        self.assertEqual(result.command.command.effective_date.isoformat(), "2026-09-22")

    def test_daily_weight_resolves_to_backend_owned_command(self):
        text = "Вес 76,3 кг"
        result = resolve(ACTOR, ORIGIN, context(text), observation_proposal(
            "set_daily_weight", text, quantity={"amount": "76.3", "unit": "kg"}))
        self.assertEqual((result.status, result.reason), ("ready", "weight_command_prepared"))
        self.assertEqual(result.command.command.kind, "set_daily_weight")
        self.assertEqual(result.command.command.value_kg, "76.3")
        self.assertIsNone(result.command.command.expected_revision_id)

    def test_daily_steps_set_and_increment_use_current_revision(self):
        text = "8200 шагов"
        source = context(text)
        source["observations"] = [{"metric": "daily_steps", "series_date": "2026-09-22",
                                   "revision_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd"}]
        set_result = resolve(ACTOR, ORIGIN, source, observation_proposal(
            "set_daily_steps", text, steps=8200))
        self.assertEqual(set_result.command.command.kind, "set_daily_steps")
        self.assertEqual(str(set_result.command.command.expected_revision_id),
                         "dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        increment_text = "ещё 500 шагов"
        increment = resolve(ACTOR, ORIGIN, context(increment_text), observation_proposal(
            "increment_daily_steps", increment_text, steps=500))
        self.assertEqual(increment.reason, "steps_baseline_missing")

    def test_observation_date_is_derived_when_source_has_today_marker(self):
        text = "Запиши за сегодня 8200 шагов"
        result = resolve(ACTOR, ORIGIN, context(text), observation_proposal(
            "set_daily_steps", text, steps=8200))
        self.assertEqual((result.status, result.reason), ("ready", "steps_command_prepared"))
        self.assertEqual(result.command.command.effective_date.isoformat(), "2026-09-22")

    def test_increment_steps_requires_existing_baseline(self):
        text = "ещё 500 шагов"
        source = context(text)
        source["observations"] = [{"metric": "daily_steps", "series_date": "2026-09-22",
                                   "revision_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd"}]
        result = resolve(ACTOR, ORIGIN, source, observation_proposal(
            "increment_daily_steps", text, steps=500))
        self.assertEqual((result.status, result.reason), ("ready", "steps_increment_prepared"))

    def test_known_dairy_builds_backend_owned_command_without_nutrition_values(self):
        result = resolve(ACTOR, ORIGIN, context(), proposal())
        self.assertEqual(result.status, "ready")
        command = result.command
        self.assertEqual(command.user_id, ACTOR)
        self.assertEqual(command.source.evidence_update_ids, [ORIGIN])
        self.assertEqual(command.command.food.components[0].product_version_id, VERSION)
        self.assertEqual(command.command.food.components[0].quantity.edible_g, "100")
        self.assertNotIn("kcal", command.model_dump_json())

    def test_common_gram_abbreviation_is_an_exact_quantity(self):
        text = TEXT.replace("100 г", "100 гр")
        result = resolve(ACTOR, ORIGIN, context(text), proposal(text))
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.command.command.food.components[0].quantity.edible_g, "100")

    def test_single_catalog_candidate_cannot_supply_missing_dairy_percentage(self):
        text = "Съела 100 г творога"
        result = resolve(ACTOR, ORIGIN, context(text), proposal(text))
        self.assertEqual((result.status, result.reason), ("unresolved", "dairy_fat_missing"))
        self.assertEqual(result.pending_food_date.isoformat(), "2026-09-22")

    def test_dairy_fat_answer_reuses_original_date_and_operation_evidence(self):
        text = "Съела 100 г творога"
        original = proposal(text)
        pending_context = context(text)
        answer_context = context("5%")
        answer_context.update({"has_reply": True, "pending_questions": {"c1": {"q1": "nutrition"}},
            "pending_candidates": [dict(answer_context["candidates"][0])],
            "pending": {"job_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                         "origin_update_id": str(ORIGIN), "proposal": original.model_dump(mode="json"),
                         "context": pending_context}})
        answer = ParserOutput.model_validate({"schema_version": "1.0", "actions": [{
            "kind": "answer_clarification", "action_id": "a1", "evidence": "5%",
            "depends_on": [], "unresolved": [],
            "pending": {"kind": "candidate", "candidate_ref": "c1", "candidate_kind": "pending"},
            "answers": [{"question_ref": "q1", "value": {"kind": "nutrition",
                "supplied_nutrition": {"kcal": None, "protein_g": None, "fat_g": "5", "carbs_g": None}}}],
        }]})
        result = resolve(ACTOR, UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), answer_context, answer)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.command.source.origin_update_id, ORIGIN)
        self.assertEqual(result.command.source.evidence_update_ids,
                         [ORIGIN, UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")])
        self.assertEqual(result.command.command.food.effective_date.isoformat(), "2026-09-22")

    def test_explicit_fat_conflict_and_multiple_percentages_never_select_candidate(self):
        for text in ("Съела 100 г творога 9%", "Съела 100 г творога 5% или 9%", "Съела 100 г творога -5%"):
            with self.subTest(text=text):
                self.assertEqual(resolve(ACTOR, ORIGIN, context(text), proposal(text)).status, "unresolved")

    def test_exact_distinctive_product_name_does_not_need_redundant_percentage(self):
        text = "Съела 100 г Творог МаркаА"
        source = context(text)
        source["candidates"][0]["name"] = "Творог МаркаА"
        self.assertEqual(resolve(ACTOR, ORIGIN, source, proposal(text)).status, "ready")
        source["candidates"][0]["declared_fat_percent"] = None
        self.assertEqual(resolve(ACTOR, ORIGIN, source, proposal(text)).status, "ready")
        source["candidates"][0]["name"] = "Творог"
        self.assertEqual(resolve(ACTOR, ORIGIN, source, proposal(text)).reason, "dairy_fat_missing")

    def test_percent_never_supplies_grams_and_unsupported_conversions_wait(self):
        for text, quantity in [("Съела творог 5%", {"amount": "5", "unit": "g"}),
                               ("Съела 0,1 кг творога 5%", {"amount": "0.1", "unit": "kg"}),
                               (TEXT, {"amount": "5", "unit": "g"})]:
            with self.subTest(text=text, quantity=quantity):
                self.assertEqual(resolve(ACTOR, ORIGIN, context(text), proposal(text, quantity=quantity)).status, "unresolved")

    def test_quantity_bounds_ranges_and_estimates_are_not_exact_portions(self):
        for prefix in ("до ", "от ", "менее ", "более ", "минимум ", "максимум ",
                       "up to ", "at least ", "<", "≥", "±", "около ", "~", "80–", "80—"):
            with self.subTest(prefix=prefix):
                text = TEXT.replace("100 г", prefix + "100 г")
                result = resolve(ACTOR, ORIGIN, context(text), proposal(text))
                self.assertEqual(result.reason, "quantity_not_exact")
                self.assertIsNone(result.command)

    def test_ambiguous_gross_or_bone_weight_waits_for_usable_weight(self):
        text = "Съела около 150 г курицы с костями"
        source = context(text)
        source["candidates"][0].update(name="Курица", food_kind="general", declared_fat_percent=None)
        result = resolve(ACTOR, ORIGIN, source, proposal(text, quantity={"amount": "150", "unit": "g"}))
        self.assertEqual((result.status, result.reason), ("unresolved", "weight_basis_unresolved"))
        self.assertEqual(result.pending_questions, {"c1": {"q1": ["quantity", "approved_estimate"]}})

    def test_explicit_estimate_answer_marks_quantity_and_approval_evidence(self):
        text = "Съела около 150 г Курицы"
        source = context(text)
        source["candidates"][0].update(name="Курица", food_kind="general", declared_fat_percent=None)
        original = proposal(text, quantity={"amount": "150", "unit": "g"})
        answer_origin = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        answer_context = context("примерно 120 г, считай так")
        answer_context.update({"has_reply": True, "pending_questions": {"c1": {"q1": ["quantity", "approved_estimate"]}},
            "pending_candidates": [dict(answer_context["candidates"][0])],
            "pending": {"job_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                         "origin_update_id": str(ORIGIN), "proposal": original.model_dump(mode="json"),
                         "context": source}})
        answer = ParserOutput.model_validate({"schema_version": "1.0", "actions": [{
            "kind": "answer_clarification", "action_id": "a1", "evidence": "примерно 120 г, считай так",
            "depends_on": [], "unresolved": [],
            "pending": {"kind": "candidate", "candidate_ref": "c1", "candidate_kind": "pending"},
            "answers": [{"question_ref": "q1", "value": {"kind": "approved_estimate",
                "quantity": {"amount": "120", "unit": "g"}}}],
        }]})
        result = resolve(ACTOR, answer_origin, answer_context, answer)
        self.assertEqual(result.status, "ready")
        component = result.command.command.food.components[0]
        self.assertEqual(component.quantity_provenance, "user_approved_estimate")
        self.assertEqual(component.approval_update_id, answer_origin)
        self.assertEqual(result.command.source.evidence_update_ids, [ORIGIN, answer_origin])

    def test_estimate_answer_without_explicit_approval_stays_unresolved(self):
        text = "Съела около 150 г Курицы"
        source = context(text)
        source["candidates"][0].update(name="Курица", food_kind="general", declared_fat_percent=None)
        original = proposal(text, quantity={"amount": "150", "unit": "g"})
        answer_context = context("120 г")
        answer_context.update({"has_reply": True, "pending_questions": {"c1": {"q1": ["quantity", "approved_estimate"]}},
            "pending_candidates": [dict(answer_context["candidates"][0])],
            "pending": {"job_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                         "origin_update_id": str(ORIGIN), "proposal": original.model_dump(mode="json"),
                         "context": source}})
        answer = ParserOutput.model_validate({"schema_version": "1.0", "actions": [{
            "kind": "answer_clarification", "action_id": "a1", "evidence": "120 г",
            "depends_on": [], "unresolved": [],
            "pending": {"kind": "candidate", "candidate_ref": "c1", "candidate_kind": "pending"},
            "answers": [{"question_ref": "q1", "value": {"kind": "approved_estimate",
                "quantity": {"amount": "120", "unit": "g"}}}],
        }]})
        result = resolve(ACTOR, UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"), answer_context, answer)
        self.assertEqual((result.status, result.reason), ("unresolved", "estimate_approval_missing"))

    def test_exact_quantity_reply_can_resume_original_approximation(self):
        text = "Съела около 150 г Курицы"
        source = context(text)
        source["candidates"][0].update(name="Курица", food_kind="general", declared_fat_percent=None)
        resumed = dict(source, source_text=text + "\n120 г", quantity_clarification_answered=True,
                       clarification_text="120 г", pending_identity_confirmed=True)
        result = resolve(ACTOR, ORIGIN, resumed, proposal(text, quantity={"amount": "120", "unit": "g"}))
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.command.command.food.components[0].quantity.edible_g, "120")

    def test_worker_explains_exact_weight_boundary(self):
        message = ConversationWorker._clarification(
            {"candidates": [{"ref": "c1", "name": "Курица"}], "recipes": []},
            "weight_basis_unresolved", {"c1": {"q1": "quantity"}})
        self.assertIn("съедобный вес", message)
        self.assertIn("не включаю", message)

    def test_unknown_catalog_classification_or_fat_is_not_invented(self):
        for field in ("food_kind", "declared_fat_percent"):
            source = context()
            source["candidates"][0][field] = None
            self.assertEqual(resolve(ACTOR, ORIGIN, source, proposal()).status, "unresolved")

    def test_lexical_decimal_quantity_and_volume_basis(self):
        text = "Выпила 125,5 мл молока 3,2%"
        source = context(text)
        source["candidates"][0].update(name="Молоко 3,2%", nutrition_basis="per_100_ml", declared_fat_percent="3.20")
        output = proposal(text, quantity={"amount": "125.5", "unit": "ml"})
        self.assertEqual(resolve(ACTOR, ORIGIN, source, output).command.command.food.components[0].quantity.ml, "125.5")
        source["candidates"][0]["nutrition_basis"] = "per_100_g"
        self.assertEqual(resolve(ACTOR, ORIGIN, source, output).reason, "unit_basis_mismatch")

    def test_dates_use_source_date_and_require_lexical_consistency(self):
        for hint, text, expected in [(None, TEXT, "2026-09-22"),
                ("вчера", "Вчера " + TEXT, "2026-09-21"), ("2026-09-20", TEXT + " 2026-09-20", "2026-09-20"),
                (None, "Вчера " + TEXT, "2026-09-21"), ("сегодня", "Вчера " + TEXT, None),
                ("вчера", "Вчера или сегодня " + TEXT, None), ("позавчера", "Позавчера " + TEXT, None),
                ("2026-02-30", TEXT + " 2026-02-30", None)]:
            with self.subTest(text=text, hint=hint):
                result = resolve(ACTOR, ORIGIN, context(text), proposal(text, date_hint={"text": hint}))
                if expected:
                    self.assertEqual(result.command.command.food.effective_date.isoformat(), expected)
                else:
                    self.assertEqual(result.status, "unresolved")

    def test_backend_uses_source_local_date_when_model_invents_date_hint(self):
        for hint in ("сегодня", "вчера", "2026-09-20", "model-invented-date"):
            with self.subTest(hint=hint):
                result = resolve(ACTOR, ORIGIN, context(TEXT), proposal(TEXT, date_hint={"text": hint}))
                self.assertEqual(result.status, "ready")
                self.assertEqual(result.command.command.food.effective_date.isoformat(), "2026-09-22")

    def test_plans_questions_and_corrections_are_not_forced_into_additions(self):
        for text in ("Планирую 100 г творога 5%", "Сколько калорий в 100 г творога 5%?",
                     "Не ела 100 г творога 5%", "Исправь на 100 г творога 5%"):
            self.assertEqual(resolve(ACTOR, ORIGIN, context(text), proposal(text)).reason, "consumption_evidence_conflict")

    def test_nonlogging_and_multi_action_have_explicit_dispositions(self):
        data = fixture()["output"]
        data["actions"] = [{"kind": "non_logging", "action_id": "a1", "evidence": TEXT,
                            "depends_on": [], "unresolved": [], "reason": "planned_food"}]
        self.assertEqual(resolve(ACTOR, ORIGIN, context(), ParserOutput.model_validate_json(json.dumps(data))).status, "non_logging")
        data = fixture()["output"]
        second = deepcopy(data["actions"][0])
        second["action_id"] = "a2"
        data["actions"].append(second)
        self.assertEqual(resolve(ACTOR, ORIGIN, context(), ParserOutput.model_validate_json(json.dumps(data))).reason, "multiple_actions")

    def test_duplicate_names_and_unknown_tokens_do_not_resolve(self):
        source = context()
        other = dict(source["candidates"][0], ref="c2", version_id=str(ORIGIN))
        source["candidates"].append(other)
        self.assertEqual(resolve(ACTOR, ORIGIN, source, proposal()).reason, "product_ambiguous")
        with self.assertRaises(ValueError):
            resolve(ACTOR, ORIGIN, context(), proposal(food={"kind": "candidate", "candidate_kind": "product", "candidate_ref": "c99"}))

    def test_adapter_context_omits_private_ids_and_cannot_mutate_snapshot(self):
        snapshot = context()
        request = parser_request(snapshot)
        self.assertNotIn(str(VERSION), repr(request.candidates))
        self.assertNotIn(TEXT, repr(request))
        request.candidates[0]["name"] = "changed"
        self.assertEqual(snapshot["candidates"][0]["name"], PRODUCT_NAME)
        parser = SyntheticParser(fixture())
        self.assertEqual(json.loads(parser.parse(parser_request(context()))), fixture()["output"])
        with self.assertRaises(ParserUnavailable):
            parser.parse(parser_request(context("unrelated text")))


if __name__ == "__main__":
    unittest.main()
