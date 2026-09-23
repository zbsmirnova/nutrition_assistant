"""Untrusted LLM proposals: no user IDs, database IDs, or calculated nutrition."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .common import (
    ActionId, CandidateReference, Contract, Count, DateHint, DescribedTarget,
    EntryTarget, FoodReference, IngredientMention, Name, PendingCandidate,
    PositiveCount, ProductTarget, QuantityMention, QuestionToken, RecipeTarget,
    SuppliedNutrition, Text, UnresolvedField, WeightBasis, Meal,
)


class Proposal(Contract):
    action_id: ActionId
    evidence: Text
    depends_on: list[ActionId]
    unresolved: list[UnresolvedField]


class AddFood(Proposal):
    kind: Literal["add_food"]
    food: FoodReference
    quantity: QuantityMention
    weight_basis: WeightBasis | None
    date_hint: DateHint
    meal: Meal


class SetQuantity(Contract):
    kind: Literal["set_quantity"]
    quantity: QuantityMention


class SetInedibleWeight(Contract):
    kind: Literal["set_inedible_weight"]
    quantity: QuantityMention


class MoveDate(Contract):
    kind: Literal["move_date"]
    date_hint: DateHint


class SetMeal(Contract):
    kind: Literal["set_meal"]
    meal: Meal


class ReplaceFood(Contract):
    kind: Literal["replace_food"]
    food: FoodReference


FoodChange = Annotated[SetQuantity | SetInedibleWeight | MoveDate | SetMeal | ReplaceFood, Field(discriminator="kind")]


class CorrectFood(Proposal):
    kind: Literal["correct_food"]
    target: EntryTarget
    change: FoodChange


class DeleteFood(Proposal):
    kind: Literal["delete_food"]
    target: EntryTarget


class UndoFood(Proposal):
    kind: Literal["undo_food"]
    target: EntryTarget


class SetWeight(Proposal):
    kind: Literal["set_daily_weight"]
    date_hint: DateHint
    quantity: QuantityMention


class SetSteps(Proposal):
    kind: Literal["set_daily_steps"]
    date_hint: DateHint
    steps: Count | None


class IncrementSteps(Proposal):
    kind: Literal["increment_daily_steps"]
    date_hint: DateHint
    steps: PositiveCount | None


class ProvidedRecipe(Contract):
    kind: Literal["provided"]
    per_100_g: SuppliedNutrition
    ingredients: list[IngredientMention]


class CalculatedRecipe(Contract):
    kind: Literal["calculate"]
    ingredients: Annotated[list[IngredientMention], Field(min_length=1, max_length=100)]
    finished_weight: QuantityMention


RecipeInput = Annotated[ProvidedRecipe | CalculatedRecipe, Field(discriminator="kind")]


class DefineRecipe(Proposal):
    kind: Literal["define_recipe"]
    name: Name | None
    cooking_instructions: Text | None
    nutrition_input: RecipeInput


class ChangeInstructions(Contract):
    kind: Literal["set_instructions"]
    cooking_instructions: Text | None


class ChangeRecipeNutrition(Contract):
    kind: Literal["set_nutrition"]
    per_100_g: SuppliedNutrition


class ChangeIngredients(Contract):
    kind: Literal["replace_ingredients"]
    ingredients: Annotated[list[IngredientMention], Field(min_length=1, max_length=100)]
    finished_weight: QuantityMention


class ChangeIngredientAmount(Contract):
    kind: Literal["set_ingredient_quantity"]
    ingredient_description: Text
    quantity: QuantityMention
    finished_weight: QuantityMention


RecipeChange = Annotated[
    ChangeInstructions | ChangeRecipeNutrition | ChangeIngredients | ChangeIngredientAmount,
    Field(discriminator="kind"),
]


class ReviseRecipe(Proposal):
    kind: Literal["revise_recipe"]
    target: RecipeTarget
    change: RecipeChange


class ProductInput(Contract):
    name: Name | None
    brand: Name | None
    nutrition_basis: Literal["per_100_g", "per_100_ml"] | None
    supplied_nutrition: SuppliedNutrition
    weight_basis: WeightBasis | None


class DefineProduct(Proposal):
    kind: Literal["define_product"]
    product: ProductInput


class ReviseProduct(Proposal):
    kind: Literal["revise_product"]
    target: ProductTarget
    product: ProductInput


class ConfirmDay(Proposal):
    kind: Literal["confirm_day_complete"]
    date_hint: DateHint
    explicit_zero_food: bool


class GetDay(Proposal):
    kind: Literal["get_day_summary"]
    date_hint: DateHint


class GetRecipe(Proposal):
    kind: Literal["get_recipe"]
    target: RecipeTarget


class FoodQuestion(Proposal):
    kind: Literal["food_question"]
    food: FoodReference
    quantity: QuantityMention
    question: Text


class NonLogging(Proposal):
    kind: Literal["non_logging"]
    reason: Literal["planned_food", "general_chat", "unsupported", "ambiguous_intent"]


class QuantityAnswer(Contract):
    kind: Literal["quantity"]
    quantity: QuantityMention


class CandidateAnswer(Contract):
    kind: Literal["selection"]
    selection: CandidateReference


class DateAnswer(Contract):
    kind: Literal["date"]
    date_hint: DateHint


class NutritionAnswer(Contract):
    kind: Literal["nutrition"]
    supplied_nutrition: SuppliedNutrition


class TextAnswer(Contract):
    kind: Literal["text"]
    text: Text


class ConfirmationAnswer(Contract):
    kind: Literal["confirmation"]
    accepted: bool


AnswerValue = Annotated[
    QuantityAnswer | CandidateAnswer | DateAnswer | NutritionAnswer | TextAnswer | ConfirmationAnswer,
    Field(discriminator="kind"),
]


class ClarificationAnswer(Contract):
    question_ref: QuestionToken
    value: AnswerValue


class AnswerClarification(Proposal):
    kind: Literal["answer_clarification"]
    pending: PendingCandidate | None
    answers: Annotated[list[ClarificationAnswer], Field(min_length=1, max_length=100)]


class CancelClarification(Proposal):
    kind: Literal["cancel_clarification"]
    pending: Annotated[PendingCandidate | DescribedTarget, Field(discriminator="kind")]


ParserAction = Annotated[
    AddFood | CorrectFood | DeleteFood | UndoFood | SetWeight | SetSteps | IncrementSteps
    | DefineRecipe | ReviseRecipe | DefineProduct | ReviseProduct | ConfirmDay | GetDay
    | GetRecipe | FoodQuestion | NonLogging | AnswerClarification | CancelClarification,
    Field(discriminator="kind"),
]


class ParserOutput(Contract):
    schema_version: Literal["1.0"]
    actions: Annotated[list[ParserAction], Field(min_length=1, max_length=32)]

    @model_validator(mode="after")
    def valid_action_graph(self) -> Self:
        actions = {item.action_id: item for item in self.actions}
        if len(actions) != len(self.actions):
            raise ValueError("action IDs must be unique within an interpretation")
        visiting, visited = set(), set()

        def visit(key: str) -> None:
            if key in visiting:
                raise ValueError("cyclic action dependencies")
            if key in visited:
                return
            visiting.add(key)
            item = actions[key]
            if len(set(item.depends_on)) != len(item.depends_on):
                raise ValueError("duplicate dependency")
            for dependency in item.depends_on:
                if dependency not in actions:
                    raise ValueError("dependency references an unknown action")
                visit(dependency)
            visiting.remove(key)
            visited.add(key)

        for key in actions:
            visit(key)

        def check_refs(value: object, item: Proposal) -> None:
            if isinstance(value, dict):
                if value.get("kind") == "action_result":
                    dependency = value["action_id"]
                    if dependency not in item.depends_on or actions[dependency].kind != "define_recipe":
                        raise ValueError("food action results must depend on a recipe definition")
                for child in value.values():
                    check_refs(child, item)
            elif isinstance(value, list):
                for child in value:
                    check_refs(child, item)

        for item in self.actions:
            check_refs(item.model_dump(), item)
        return self


def validate_parser_context(
    output: ParserOutput,
    candidates: dict[str, str],
    pending_questions: dict[str, dict[str, str]],
    *,
    source_text: str,
    has_reply: bool = False,
) -> None:
    """Check opaque references against backend context, not against database contents.

    Candidate ownership, transcript evidence, and whether an action is executable
    still require backend resolution. A structurally valid output is untrusted.
    """
    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("kind") == "candidate":
                expected_kind = candidates.get(value["candidate_ref"])
                if (isinstance(expected_kind, (set, frozenset))
                        and value["candidate_kind"] not in expected_kind) or (
                            not isinstance(expected_kind, (set, frozenset))
                            and expected_kind != value["candidate_kind"]):
                    raise ValueError("candidate missing from scoped context or of the wrong type")
            if value.get("kind") == "reply" and not has_reply:
                raise ValueError("no reply-to context exists")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(output.model_dump())
    for action in output.actions:
        if action.evidence not in source_text:
            raise ValueError("evidence must be a literal excerpt from the source message")
        if isinstance(action, AnswerClarification) and action.pending is not None:
            expected = pending_questions.get(action.pending.candidate_ref, {})
            seen = set()
            for answer in action.answers:
                if answer.question_ref in seen:
                    raise ValueError("question answered more than once")
                seen.add(answer.question_ref)
                accepted = expected.get(answer.question_ref)
                if isinstance(accepted, (list, tuple, set, frozenset)):
                    valid = answer.value.kind in accepted
                else:
                    valid = accepted == answer.value.kind
                if not valid:
                    raise ValueError("question missing from pending action or answer type mismatches")
