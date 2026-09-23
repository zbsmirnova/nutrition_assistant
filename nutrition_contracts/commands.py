"""Backend-resolved commands. These types are never an LLM output interface."""

from datetime import date
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from .common import (
    Contract, Count, Meal, Name, NormalizedQuantity,
    NutritionSnapshot, PositiveCount, PositiveDecimal, SourceQuantity,
    Text, TimeZoneName, WeightBasis,
)


class ProductComponent(Contract):
    kind: Literal["product"]
    description: Name
    product_version_id: UUID
    quantity: NormalizedQuantity


class RecipeComponent(Contract):
    kind: Literal["recipe"]
    description: Name
    recipe_version_id: UUID
    eaten_grams: PositiveDecimal


class EstimatedComponent(Contract):
    kind: Literal["approved_estimate"]
    description: Name
    estimate_source_id: UUID
    approval_update_id: UUID
    quantity: NormalizedQuantity


Component = Annotated[ProductComponent | RecipeComponent | EstimatedComponent, Field(discriminator="kind")]


class FoodState(Contract):
    effective_date: date
    time_zone: TimeZoneName
    meal: Meal
    description: Text
    components: Annotated[list[Component], Field(min_length=1, max_length=100)]


class AddConsumedFood(Contract):
    kind: Literal["add_consumed_food"]
    food: FoodState


class CorrectFoodEntry(Contract):
    """A complete replacement snapshot; unaffected components must be preserved."""

    kind: Literal["correct_food_entry"]
    entry_id: UUID
    expected_revision_id: UUID
    replacement: FoodState
    reason: Text


class DeleteFoodEntry(Contract):
    kind: Literal["delete_food_entry"]
    entry_id: UUID
    expected_revision_id: UUID
    reason: Text


class RestoreFoodEntry(Contract):
    kind: Literal["restore_food_entry"]
    entry_id: UUID
    expected_revision_id: UUID
    restore_from_revision_id: UUID


class DailyCommand(Contract):
    effective_date: date
    time_zone: TimeZoneName


class SetDailyWeight(DailyCommand):
    kind: Literal["set_daily_weight"]
    value_kg: PositiveDecimal
    expected_revision_id: UUID | None


class SetDailySteps(DailyCommand):
    kind: Literal["set_daily_steps"]
    steps: Count
    expected_revision_id: UUID | None


class IncrementDailySteps(DailyCommand):
    kind: Literal["increment_daily_steps"]
    steps: PositiveCount
    expected_revision_id: UUID


class ResolvedIngredientSource(Contract):
    kind: Literal["resolved"]
    product_version_id: UUID
    quantity: NormalizedQuantity


class UnknownIngredientSource(Contract):
    kind: Literal["unknown"]
    reason: Text


class RecipeIngredient(Contract):
    name_as_entered: Name
    original_quantity: SourceQuantity
    weight_basis: WeightBasis | None
    source: Annotated[ResolvedIngredientSource | UnknownIngredientSource, Field(discriminator="kind")]


class ProvidedRecipeNutrition(Contract):
    kind: Literal["provided"]
    data_source_id: UUID
    per_100_g: NutritionSnapshot


class CalculatedRecipeNutrition(Contract):
    """Inputs for deterministic backend arithmetic; no model-computed result."""

    kind: Literal["calculate"]
    finished_yield_g: PositiveDecimal
    yield_basis: Literal["measured", "ingredient_sum_no_evaporation", "user_confirmed_estimate"]
    estimate_approval_update_id: UUID | None
    calculation_policy_version: Name

    @model_validator(mode="after")
    def estimated_yield_requires_approval(self) -> Self:
        if (self.yield_basis == "user_confirmed_estimate") != (self.estimate_approval_update_id is not None):
            raise ValueError("estimated yield requires an approval update; measured yield does not")
        return self


class RecipeDefinition(Contract):
    name: Name
    cooking_instructions: Text | None
    ingredients: Annotated[list[RecipeIngredient], Field(max_length=100)]
    nutrition: Annotated[ProvidedRecipeNutrition | CalculatedRecipeNutrition, Field(discriminator="kind")]

    @model_validator(mode="after")
    def calculation_has_ingredients(self) -> Self:
        if isinstance(self.nutrition, CalculatedRecipeNutrition) and not self.ingredients:
            raise ValueError("recipe calculation requires ingredients")
        return self


class DefineRecipe(Contract):
    kind: Literal["define_recipe"]
    recipe: RecipeDefinition


class ReviseRecipe(Contract):
    kind: Literal["revise_recipe"]
    recipe_id: UUID
    expected_version_id: UUID
    replacement: RecipeDefinition


class ProductDefinition(Contract):
    name: Name
    brand: Name | None
    data_source_id: UUID
    nutrition_basis: Literal["per_100_g", "per_100_ml"]
    nutrition: NutritionSnapshot
    weight_basis: WeightBasis
    grams_per_piece: PositiveDecimal | None
    ml_per_piece: PositiveDecimal | None
    density_g_per_ml: PositiveDecimal | None


class DefineProduct(Contract):
    kind: Literal["define_product"]
    product: ProductDefinition


class ReviseProduct(Contract):
    kind: Literal["revise_product"]
    product_id: UUID
    expected_version_id: UUID
    replacement: ProductDefinition


class ConfirmDayComplete(DailyCommand):
    kind: Literal["confirm_day_complete"]
    expected_day_revision: Count
    intake_declaration: Literal["logged_food", "explicit_zero_food"]


class GetDaySummary(DailyCommand):
    kind: Literal["get_day_summary"]


class GetRecipe(Contract):
    kind: Literal["get_recipe"]
    recipe_id: UUID


class PreviewFood(Contract):
    """Read-only calculation. Never inserts a food entry."""

    kind: Literal["preview_food"]
    components: Annotated[list[Component], Field(min_length=1, max_length=100)]


class CancelPendingAction(Contract):
    kind: Literal["cancel_pending_action"]
    pending_action_id: UUID
    expected_pending_revision: PositiveCount


class DismissDailyCheckIn(DailyCommand):
    kind: Literal["dismiss_daily_check_in"]
    check_in_id: UUID


ApplicationCommand = Annotated[
    AddConsumedFood | CorrectFoodEntry | DeleteFoodEntry | RestoreFoodEntry | SetDailyWeight
    | SetDailySteps | IncrementDailySteps | DefineRecipe | ReviseRecipe | DefineProduct
    | ReviseProduct | ConfirmDayComplete | GetDaySummary | GetRecipe | PreviewFood
    | CancelPendingAction | DismissDailyCheckIn,
    Field(discriminator="kind"),
]


class CommandSource(Contract):
    origin_update_id: UUID
    evidence_update_ids: Annotated[list[UUID], Field(min_length=1, max_length=100)]
    pending_action_id: UUID | None

    @model_validator(mode="after")
    def source_is_retained(self) -> Self:
        if len(set(self.evidence_update_ids)) != len(self.evidence_update_ids):
            raise ValueError("duplicate evidence update")
        if self.origin_update_id not in self.evidence_update_ids:
            raise ValueError("evidence must include the original update")
        return self


class CommandEnvelope(Contract):
    schema_version: Literal["1.0"]
    user_id: UUID
    operation_id: UUID
    source: CommandSource
    context_revision: Count
    command: ApplicationCommand

    @model_validator(mode="after")
    def approvals_are_evidenced(self) -> Self:
        evidence = set(self.source.evidence_update_ids)

        def check(value: object) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"approval_update_id", "estimate_approval_update_id"}:
                        if child is not None and child not in evidence:
                            raise ValueError("approval must be part of the command's source evidence")
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        check(self.command.model_dump())
        return self
