"""Backend outcomes, including honest partial nutrition coverage."""

from datetime import date
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from .commands import RecipeIngredient
from .common import (
    CandidateReference, Contract, Count, DecimalText, Name, NutrientValue,
    NutritionSnapshot, PositiveCount, PositiveDecimal, QuestionToken, Text,
)


class CompleteTotal(Contract):
    kind: Literal["complete"]
    amount: NutrientValue
    known_components: PositiveCount


class PartialTotal(Contract):
    kind: Literal["partial"]
    known_subtotal: DecimalText
    known_components: PositiveCount
    unknown_components: PositiveCount


class UnknownTotal(Contract):
    kind: Literal["unknown"]
    unknown_components: PositiveCount


class EmptyTotal(Contract):
    kind: Literal["empty"]


NutrientTotal = Annotated[CompleteTotal | PartialTotal | UnknownTotal | EmptyTotal, Field(discriminator="kind")]


class DayNutrition(Contract):
    kcal: NutrientTotal
    protein_g: NutrientTotal
    fat_g: NutrientTotal
    carbs_g: NutrientTotal


class DailySummary(Contract):
    effective_date: date
    completeness: Literal["unconfirmed", "complete"]
    explicit_zero_food: bool
    pending_food_actions: Count
    entry_count: Count
    component_count: Count
    nutrition: DayNutrition

    @model_validator(mode="after")
    def consistent_coverage(self) -> Self:
        if self.entry_count > self.component_count or (self.entry_count == 0) != (self.component_count == 0):
            raise ValueError("active entries require at least one component each")
        if self.explicit_zero_food and (self.entry_count != 0 or self.completeness != "complete"):
            raise ValueError("explicit zero intake requires an empty, confirmed day")
        for nutrient in (self.nutrition.kcal, self.nutrition.protein_g, self.nutrition.fat_g, self.nutrition.carbs_g):
            count = getattr(nutrient, "known_components", 0) + getattr(nutrient, "unknown_components", 0)
            if count != self.component_count:
                raise ValueError("nutrient coverage must account for every active component")
        return self


class MutationReceipt(Contract):
    entity_kind: Literal["food_entry", "recipe", "product", "daily_weight", "daily_steps", "food_day", "pending_action", "check_in"]
    entity_id: UUID
    revision_id: UUID | None
    effective_date: date | None

    @model_validator(mode="after")
    def dated_entity_has_date(self) -> Self:
        if self.entity_kind in {"food_entry", "daily_weight", "daily_steps", "food_day", "check_in"} and self.effective_date is None:
            raise ValueError("a dated entity requires its effective date")
        return self


class FoodEntrySummary(Contract):
    entry_id: UUID
    revision_id: UUID
    effective_date: date
    description: Text
    nutrition: NutritionSnapshot | None
    change: Literal["added", "corrected", "deleted", "restored"]
    estimated: bool = False

    @model_validator(mode="after")
    def deleted_entry_has_no_nutrition(self) -> Self:
        if (self.change == "deleted") != (self.nutrition is None):
            raise ValueError("only a deleted entry omits its nutrition snapshot")
        return self


class RecipeProfile(Contract):
    recipe_id: UUID
    version_id: UUID
    name: Name
    ingredients: list[RecipeIngredient]
    cooking_instructions: Text | None
    per_100_g: NutritionSnapshot


class WeightSnapshot(Contract):
    kind: Literal["daily_weight"]
    observation_id: UUID
    revision_id: UUID
    effective_date: date
    value_kg: PositiveDecimal


class StepsSnapshot(Contract):
    kind: Literal["daily_steps"]
    observation_id: UUID
    revision_id: UUID
    effective_date: date
    steps: Count


ObservationSnapshot = Annotated[WeightSnapshot | StepsSnapshot, Field(discriminator="kind")]


class ResultBase(Contract):
    schema_version: Literal["1.0"]
    operation_id: UUID


class Applied(ResultBase):
    outcome: Literal["applied"]
    mutations: Annotated[list[MutationReceipt], Field(min_length=1)]
    food_entries: list[FoodEntrySummary]
    observations: list[ObservationSnapshot]
    daily_summaries: list[DailySummary]
    recipe: RecipeProfile | None

    @model_validator(mode="after")
    def food_changes_have_summaries(self) -> Self:
        if len({(item.entity_kind, item.entity_id) for item in self.mutations}) != len(self.mutations):
            raise ValueError("duplicate mutation receipt")
        food = {item.entity_id: item for item in self.mutations if item.entity_kind == "food_entry"}
        entries = {item.entry_id: item for item in self.food_entries}
        if len(entries) != len(self.food_entries) or set(food) != set(entries):
            raise ValueError("each changed food entry needs exactly one entry summary")
        days = [item.effective_date for item in self.daily_summaries]
        if len(set(days)) != len(days):
            raise ValueError("duplicate day summary")
        for key, receipt in food.items():
            entry = entries[key]
            if entry.revision_id != receipt.revision_id or entry.effective_date != receipt.effective_date:
                raise ValueError("food summary must match its mutation receipt")
            if entry.effective_date not in days:
                raise ValueError("food changes require updated daily totals")
        expected_observations = {
            (m.entity_kind, m.entity_id): m for m in self.mutations
            if m.entity_kind in {"daily_weight", "daily_steps"}
        }
        actual_observations = {(o.kind, o.observation_id): o for o in self.observations}
        if len(actual_observations) != len(self.observations) or set(expected_observations) != set(actual_observations):
            raise ValueError("each changed daily observation requires its resulting value")
        for key, receipt in expected_observations.items():
            observation = actual_observations[key]
            if observation.revision_id != receipt.revision_id or observation.effective_date != receipt.effective_date:
                raise ValueError("observation snapshot must match its mutation receipt")
        return self


class NoChange(ResultBase):
    outcome: Literal["no_change"]
    reason: Literal["same_value", "already_complete", "already_cancelled", "already_dismissed"]
    daily_summaries: list[DailySummary]


class Question(Contract):
    question_ref: QuestionToken
    field: Name
    prompt: Text
    answer_kind: Literal["quantity", "selection", "date", "nutrition", "text", "confirmation"]
    choices: list[CandidateReference]


class NeedsClarification(ResultBase):
    outcome: Literal["needs_clarification"]
    pending_action_id: UUID
    pending_revision: PositiveCount
    effective_date: date | None
    questions: Annotated[list[Question], Field(min_length=1)]
    previously_applied_operation_ids: list[UUID]

    @model_validator(mode="after")
    def unique_questions(self) -> Self:
        if len({q.question_ref for q in self.questions}) != len(self.questions):
            raise ValueError("question references must be unique per pending revision")
        if len(set(self.previously_applied_operation_ids)) != len(self.previously_applied_operation_ids):
            raise ValueError("duplicate previously applied operation")
        if self.operation_id in self.previously_applied_operation_ids:
            raise ValueError("a pending operation cannot already have been applied")
        return self


class Rejected(ResultBase):
    outcome: Literal["rejected"]
    code: Literal["invalid_input", "not_found", "unauthorized", "revision_conflict", "unsupported"]
    message: Text


class ReadDay(ResultBase):
    outcome: Literal["day_summary"]
    summary: DailySummary


class ReadRecipe(ResultBase):
    outcome: Literal["recipe_profile"]
    recipe: RecipeProfile


class FoodPreview(ResultBase):
    outcome: Literal["food_preview"]
    nutrition: NutritionSnapshot


Outcome = Annotated[
    Applied | NoChange | NeedsClarification | Rejected | ReadDay | ReadRecipe | FoodPreview,
    Field(discriminator="outcome"),
]


class OutcomeEnvelope(Contract):
    result: Outcome
