"""Trusted local catalog provisioning for the private MVP pilot."""

from decimal import Decimal
from uuid import UUID, uuid4

import sqlalchemy as sa
from pydantic import TypeAdapter, ValidationError

from nutrition_contracts.commands import RecipeIngredient, UnknownIngredientSource
from nutrition_contracts.common import DecimalText, Name, NutrientValue, NutritionSnapshot, SourceQuantity, Text

from . import schema as db
from .errors import ApplicationError
from .nutrition import to_columns
from .service import FoodService


NUTRIENTS = ("kcal", "protein_g", "fat_g", "carbs_g")


def _snapshot(values: dict[str, str | None]) -> NutritionSnapshot:
    if not any(value is not None for value in values.values()):
        raise ApplicationError("Provide at least one nutrition value")
    nutrients = {}
    adapter = TypeAdapter(DecimalText)
    for name in NUTRIENTS:
        value = values.get(name)
        if value is None:
            nutrients[name] = None
            continue
        try:
            text = adapter.validate_python(value)
            nutrients[name] = NutrientValue(value=text, lower=None, upper=None)
        except ValidationError:
            raise ApplicationError(f"Invalid non-negative decimal for {name}") from None
    return NutritionSnapshot(**nutrients)


def create_product(
    engine,
    actor: UUID,
    *,
    name: str,
    nutrition: dict[str, str | None],
    nutrition_basis: str = "per_100_g",
    weight_basis: str = "as_sold",
    food_kind: str = "general",
    declared_fat_percent: str | None = None,
) -> dict:
    """Create one immutable private product version for local pilot setup.

    This is an operator-only provisioning path. It records supplied nutrition as
    an explicit user-owned source and never lets the parser create catalog data.
    """
    try:
        product_name = TypeAdapter(Name).validate_python(name)
    except ValidationError:
        raise ApplicationError("Product name must be a non-empty value") from None
    if nutrition_basis not in {"per_100_g", "per_100_ml"}:
        raise ApplicationError("Nutrition basis must be per_100_g or per_100_ml")
    if weight_basis not in {"raw", "cooked", "as_sold"}:
        raise ApplicationError("Weight basis must be raw, cooked, or as_sold")
    if food_kind not in {"general", "dairy"}:
        raise ApplicationError("Food kind must be general or dairy")
    fat = None
    if declared_fat_percent is not None:
        try:
            fat = Decimal(TypeAdapter(DecimalText).validate_python(declared_fat_percent))
        except (ValidationError, ValueError):
            raise ApplicationError("Declared fat percentage must be a non-negative decimal") from None
        if fat > 100 or abs(fat.as_tuple().exponent) > 2:
            raise ApplicationError("Declared fat percentage must be between 0 and 100 with at most 2 decimals")
        if food_kind != "dairy":
            raise ApplicationError("Declared fat percentage requires food kind dairy")
    snapshot = _snapshot(nutrition)
    product_id, version_id, source_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        FoodService._user(connection, actor)
        connection.execute(db.data_sources.insert().values(
            id=source_id, user_id=actor, kind="operator_catalog",
            evidence={"entered_by": "trusted_local_operator", "basis": "supplied_nutrition"}))
        connection.execute(db.products.insert().values(
            id=product_id, user_id=actor, current_version_id=version_id))
        connection.execute(db.product_versions.insert().values(
            id=version_id, user_id=actor, product_id=product_id, version_no=1,
            name=product_name, data_source_id=source_id,
            nutrition_basis=nutrition_basis, weight_basis=weight_basis,
            food_kind=food_kind, declared_fat_percent=fat,
            **to_columns(snapshot)))
    return {"product_id": str(product_id), "version_id": str(version_id), "name": product_name}


def _recipe_ingredients(values: list[dict] | None) -> list[RecipeIngredient]:
    """Validate operator-entered ingredient snapshots without resolving catalog data."""
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 100:
        raise ApplicationError("Recipe ingredients must be a JSON array with at most 100 items")
    ingredients = []
    for item in values:
        if not isinstance(item, dict):
            raise ApplicationError("Each recipe ingredient must be an object")
        try:
            name = TypeAdapter(Name).validate_python(item["name"])
            quantity = SourceQuantity(amount=item["amount"], unit=item["unit"])
            basis = item.get("weight_basis")
            if basis not in {None, "raw", "cooked", "as_sold"}:
                raise ValueError("invalid weight basis")
            ingredients.append(RecipeIngredient(
                name_as_entered=name,
                original_quantity=quantity,
                weight_basis=basis,
                source=UnknownIngredientSource(kind="unknown", reason="operator-supplied ingredient snapshot"),
            ))
        except (KeyError, TypeError, ValueError, ValidationError):
            raise ApplicationError(
                "Each ingredient needs name, positive amount, unit, and optional weight_basis"
            ) from None
    return ingredients


def create_recipe(
    engine,
    actor: UUID,
    *,
    name: str,
    nutrition: dict[str, str | None],
    ingredients: list[dict] | None = None,
    cooking_instructions: str | None = None,
) -> dict:
    """Create one owner-scoped recipe profile for trusted local pilot setup.

    Nutrition is explicitly supplied per 100 g. Ingredient rows are retained as
    un-resolved snapshots; this command never looks up products or lets a model
    create catalog data.
    """
    try:
        recipe_name = TypeAdapter(Name).validate_python(name)
        instructions = (None if cooking_instructions is None else
                        TypeAdapter(Text).validate_python(cooking_instructions))
    except ValidationError:
        raise ApplicationError("Recipe name and instructions must be non-empty values") from None
    snapshot = _snapshot(nutrition)
    recipe_ingredients = _recipe_ingredients(ingredients)
    recipe_id, version_id, source_id = uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        FoodService._user(connection, actor)
        connection.execute(db.data_sources.insert().values(
            id=source_id, user_id=actor, kind="operator_catalog",
            evidence={"entered_by": "trusted_local_operator", "basis": "supplied_recipe_nutrition"}))
        connection.execute(db.recipes.insert().values(
            id=recipe_id, user_id=actor, current_version_id=version_id))
        connection.execute(db.recipe_versions.insert().values(
            id=version_id, user_id=actor, recipe_id=recipe_id, version_no=1,
            name=recipe_name, cooking_instructions=instructions, nutrition_kind="provided",
            data_source_id=source_id, **to_columns(snapshot)))
        for position, ingredient in enumerate(recipe_ingredients):
            connection.execute(db.recipe_ingredients.insert().values(
                id=uuid4(), user_id=actor, recipe_version_id=version_id, position=position,
                name_as_entered=ingredient.name_as_entered,
                original_quantity=ingredient.original_quantity.model_dump(mode="json"),
                weight_basis=ingredient.weight_basis,
                source=ingredient.source.model_dump(mode="json")))
    return {"recipe_id": str(recipe_id), "version_id": str(version_id), "name": recipe_name}
