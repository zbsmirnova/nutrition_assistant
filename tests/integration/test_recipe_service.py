"""W011: immutable recipe persistence and backend-owned profile calculation."""
from datetime import date
from decimal import Decimal
import unittest

import sqlalchemy as sa

import test_food_service as food_tests
from nutrition_app import schema as db
from nutrition_app.demo import message
from nutrition_app.errors import Conflict
from nutrition_app.service import FoodService, operation_id_for
from nutrition_contracts.commands import (
    AddConsumedFood, CalculatedRecipeNutrition, CommandEnvelope, CommandSource, DefineRecipe, ReviseRecipe,
    FoodState, RecipeComponent, RecipeDefinition, RecipeIngredient, ResolvedIngredientSource, UnknownIngredientSource,
    ProvidedRecipeNutrition,
)
from nutrition_contracts.common import Mass, NutrientValue, NutritionSnapshot, SourceQuantity


def snapshot(kcal="70", protein="4", fat="2", carbs="9"):
    return NutritionSnapshot(**{
        key: NutrientValue(value=value, lower=None, upper=None)
        for key, value in zip(("kcal", "protein_g", "fat_g", "carbs_g"), (kcal, protein, fat, carbs))
    })


class RecipePersistenceTests(unittest.TestCase):
    cleanup_database = food_tests.FoodPersistenceTests.cleanup_database
    count = food_tests.FoodPersistenceTests.count

    def setUp(self):
        food_tests.FoodPersistenceTests.setUp(self)

    def _source(self, number, text="Сохрани рецепт"):
        return self.service.accept_message(self.seed.user_id, message(self.seed, number, text=text))

    def _provided(self, name="мой суп", instructions="Варить 30 минут."):
        return RecipeDefinition(name=name, cooking_instructions=instructions, ingredients=[
            RecipeIngredient(name_as_entered="овсяные хлопья", original_quantity=SourceQuantity(amount="93", unit="g"),
                             weight_basis="raw", source=UnknownIngredientSource(kind="unknown", reason="fixture")),
            RecipeIngredient(name_as_entered="вода", original_quantity=SourceQuantity(amount="375", unit="ml"),
                             weight_basis=None, source=UnknownIngredientSource(kind="unknown", reason="fixture")),
        ], nutrition=ProvidedRecipeNutrition(kind="provided", data_source_id=self.seed.source_id,
                                              per_100_g=snapshot()))

    def _envelope(self, source, command, context_revision=0):
        return CommandEnvelope(schema_version="1.0", user_id=self.seed.user_id,
            operation_id=operation_id_for(source), context_revision=context_revision,
            source=CommandSource(origin_update_id=source, evidence_update_ids=[source], pending_action_id=None),
            command=command)

    def test_define_recipe_persists_original_ingredients_and_profile(self):
        source = self._source(1)
        result = self.service.apply(self.seed.user_id, self._envelope(
            source, DefineRecipe(kind="define_recipe", recipe=self._provided()))).result
        self.assertIsNotNone(result.recipe)
        profile = result.recipe
        self.assertEqual(profile.name, "мой суп")
        self.assertEqual(profile.per_100_g.kcal.value, "70")
        self.assertEqual(profile.ingredients[0].original_quantity.amount, "93")
        self.assertEqual(profile.ingredients[1].original_quantity.unit, "ml")
        self.assertEqual(self.service.get_recipe(self.seed.user_id, profile.recipe_id), profile)
        self.assertEqual(self.count(db.recipes), 1)
        self.assertEqual(self.count(db.recipe_versions), 1)
        self.assertEqual(self.count(db.recipe_ingredients), 2)

    def test_calculated_recipe_uses_pinned_mass_source_and_preserves_source_snapshot(self):
        source = self._source(1, text="Сохрани рассчитанный рецепт")
        recipe = RecipeDefinition(name="каша", cooking_instructions=None, ingredients=[
            RecipeIngredient(name_as_entered="Synthetic product A", original_quantity=SourceQuantity(amount="50", unit="g"),
                weight_basis="as_sold", source=ResolvedIngredientSource(kind="resolved",
                    product_version_id=self.seed.version_id,
                    quantity=Mass(kind="mass", edible_g="50", gross_g=None, inedible_g=None, weight_basis="as_sold"))),
        ], nutrition=CalculatedRecipeNutrition(kind="calculate", finished_yield_g="100",
            yield_basis="measured", estimate_approval_update_id=None, calculation_policy_version="recipe-components-v1"))
        result = self.service.apply(self.seed.user_id, self._envelope(
            source, DefineRecipe(kind="define_recipe", recipe=recipe))).result
        self.assertEqual(result.recipe.per_100_g.kcal.value, "50")
        self.assertEqual(result.recipe.ingredients[0].source.product_version_id, self.seed.version_id)
        with self.engine.connect() as connection:
            row = connection.execute(sa.select(db.recipe_versions).where(
                db.recipe_versions.c.user_id == self.seed.user_id)).mappings().one()
        self.assertEqual(row["yield_basis"], "measured")
        self.assertEqual(str(row["finished_yield_g"]), "100.000000")

    def test_revision_creates_new_version_and_rejects_stale_revision(self):
        source = self._source(1)
        first = self.service.apply(self.seed.user_id, self._envelope(
            source, DefineRecipe(kind="define_recipe", recipe=self._provided()))).result.recipe
        revision_source = self._source(2, text="Обнови рецепт")
        replacement = self._provided(name="мой суп", instructions="Охладить.")
        revised = self.service.apply(self.seed.user_id, self._envelope(
            revision_source, ReviseRecipe(kind="revise_recipe", recipe_id=first.recipe_id,
                expected_version_id=first.version_id, replacement=replacement), context_revision=1)).result.recipe
        self.assertEqual(revised.recipe_id, first.recipe_id)
        self.assertNotEqual(revised.version_id, first.version_id)
        self.assertEqual(revised.cooking_instructions, "Охладить.")
        self.assertEqual(self.count(db.recipe_versions), 2)
        stale_source = self._source(3, text="Снова обнови")
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, self._envelope(
                stale_source, ReviseRecipe(kind="revise_recipe", recipe_id=first.recipe_id,
                    expected_version_id=first.version_id, replacement=replacement), context_revision=2))

    def test_consumption_pins_recipe_version_and_survives_recipe_revision(self):
        definition_source = self._source(1)
        first = self.service.apply(self.seed.user_id, self._envelope(
            definition_source, DefineRecipe(kind="define_recipe", recipe=self._provided()))).result.recipe
        eaten_source = self._source(2, text="Съела 250 г моего супа")
        eaten = AddConsumedFood(kind="add_consumed_food", food=FoodState(
            effective_date=date(2026, 9, 22), time_zone="Europe/Berlin", meal="lunch",
            description="мой суп", components=[RecipeComponent(kind="recipe", description="мой суп",
                recipe_version_id=first.version_id, eaten_grams="250")]))
        first_meal = self.service.apply(self.seed.user_id, self._envelope(
            eaten_source, eaten, context_revision=1)).result
        self.assertEqual(first_meal.food_entries[0].nutrition.kcal.value, "175")
        revised_source = self._source(3, text="Обнови калорийность супа")
        replacement = self._provided()
        replacement.nutrition.per_100_g.kcal = NutrientValue(value="100", lower=None, upper=None)
        revised = self.service.apply(self.seed.user_id, self._envelope(
            revised_source, ReviseRecipe(kind="revise_recipe", recipe_id=first.recipe_id,
                expected_version_id=first.version_id, replacement=replacement), context_revision=2)).result.recipe
        current_meal_source = self._source(4, text="Съела 250 г моего супа снова")
        current_meal = self.service.apply(self.seed.user_id, self._envelope(
            current_meal_source, AddConsumedFood(kind="add_consumed_food", food=FoodState(
                effective_date=date(2026, 9, 22), time_zone="Europe/Berlin", meal="dinner",
                description="мой суп", components=[RecipeComponent(kind="recipe", description="мой суп",
                    recipe_version_id=revised.version_id, eaten_grams="250")])), context_revision=3)).result
        self.assertEqual(current_meal.food_entries[0].nutrition.kcal.value, "250")
        self.assertEqual(self.service.get_entry(self.seed.user_id, first_meal.food_entries[0].entry_id).nutrition.kcal.value, "175")
        with self.engine.connect() as connection:
            row = connection.execute(sa.select(db.food_components).where(
                db.food_components.c.user_id == self.seed.user_id,
                db.food_components.c.recipe_version_id == first.version_id)).mappings().one()
        self.assertIsNone(row["product_version_id"])
        self.assertEqual(row["component_kind"], "recipe")


if __name__ == "__main__":
    unittest.main()
