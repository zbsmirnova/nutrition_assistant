"""Trusted local catalog provisioning for the private MVP pilot."""

from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from uuid import UUID, uuid4

import sqlalchemy as sa
from pydantic import TypeAdapter, ValidationError

from nutrition_contracts.commands import RecipeIngredient, UnknownIngredientSource
from nutrition_contracts.common import DecimalText, Name, NutrientValue, NutritionSnapshot, SourceQuantity, Text

from . import schema as db
from .errors import ApplicationError
from .food_sources import ExternalFoodCandidate
from .nutrition import decimal_text, to_columns
from .service import FoodService


NUTRIENTS = ("kcal", "protein_g", "fat_g", "carbs_g")
ORDINARY_UNCERTAINTY = Decimal("0.10")


def _external_evidence(candidate: ExternalFoodCandidate, query: str) -> dict:
    return {
        "provider": candidate.provider,
        "external_id": candidate.external_id,
        "source_name": candidate.source_name or candidate.name,
        "query": query.strip(),
        "license": candidate.license,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def cache_external_products(engine, actor: UUID, *, query: str,
                            candidates: list[ExternalFoodCandidate]) -> list[dict]:
    """Persist untrusted source results as private, unconfirmed catalog candidates.

    The source snapshot is immutable.  Repeated searches for the same provider
    identifier reuse the existing product version instead of creating duplicate
    local products.  No food entry is written here; the worker must receive an
    explicit user selection before approving a candidate.
    """
    try:
        product_name = TypeAdapter(Name).validate_python(query.strip())
    except ValidationError:
        raise ApplicationError("External lookup query must be a non-empty value") from None
    if not candidates:
        return []
    results = []
    with engine.begin() as connection:
        FoodService._user(connection, actor)
        source_rows = connection.execute(sa.select(db.data_sources).where(
            db.data_sources.c.user_id == actor,
            db.data_sources.c.kind == "external_catalog")).mappings().all()
        by_external = {}
        for source in source_rows:
            evidence = source["evidence"] or {}
            key = (evidence.get("provider"), str(evidence.get("external_id", "")))
            if key[0] and key[1]:
                by_external[key] = source
        confirmed_versions = set(connection.execute(sa.select(
            db.product_confirmations.c.product_version_id).where(
                db.product_confirmations.c.user_id == actor)).scalars().all())
        for candidate in candidates:
            if not isinstance(candidate, ExternalFoodCandidate) or not candidate.usable():
                continue
            if (candidate.nutrition_basis not in {"per_100_g", "per_100_ml"}
                    or candidate.weight_basis not in {"raw", "cooked", "as_sold"}
                    or candidate.food_kind not in {"general", "dairy"}):
                continue
            if candidate.declared_fat_percent is not None:
                try:
                    declared_fat = Decimal(candidate.declared_fat_percent)
                except (TypeError, ValueError, InvalidOperation):
                    continue
                if declared_fat < 0 or declared_fat > 100 or abs(declared_fat.as_tuple().exponent) > 2:
                    continue
            key = (candidate.provider, candidate.external_id)
            source = by_external.get(key)
            if source is None:
                source_id, product_id, version_id = uuid4(), uuid4(), uuid4()
                connection.execute(db.data_sources.insert().values(
                    id=source_id, user_id=actor, kind="external_catalog",
                    evidence=_external_evidence(candidate, query)))
                connection.execute(db.products.insert().values(
                    id=product_id, user_id=actor, current_version_id=version_id))
                connection.execute(db.product_versions.insert().values(
                    id=version_id, user_id=actor, product_id=product_id, version_no=1,
                    name=product_name, data_source_id=source_id,
                    nutrition_basis=candidate.nutrition_basis,
                    weight_basis=candidate.weight_basis,
                    food_kind=("dairy" if candidate.declared_fat_percent is not None else candidate.food_kind),
                    declared_fat_percent=(None if candidate.declared_fat_percent is None
                                         else declared_fat),
                    **to_columns(_snapshot({name: getattr(candidate, name) for name in NUTRIENTS}))))
                source = {"id": source_id, "evidence": _external_evidence(candidate, query)}
                by_external[key] = source
            version = connection.execute(sa.select(db.product_versions).where(
                db.product_versions.c.user_id == actor,
                db.product_versions.c.data_source_id == source["id"])).mappings().one()
            evidence = source["evidence"] or {}
            results.append({"version_id": str(version["id"]), "name": version["name"],
                            "source_kind": "external_catalog", "external_unconfirmed": version["id"] not in confirmed_versions,
                            "source_name": evidence.get("source_name") or version["name"],
                            "provider": evidence.get("provider"), "external_id": evidence.get("external_id"),
                            "nutrition_basis": version["nutrition_basis"], "weight_basis": version["weight_basis"],
                            "food_kind": version["food_kind"],
                            "declared_fat_percent": (None if version["declared_fat_percent"] is None
                                                       else str(version["declared_fat_percent"]))})
    return results


def approve_external_product(engine, actor: UUID, version_id: UUID, *, confirmed_by_update: UUID | None = None) -> None:
    """Record user approval separately from the immutable source snapshot."""
    with engine.begin() as connection:
        FoodService._user(connection, actor)
        row = connection.execute(sa.select(db.product_versions.c.data_source_id).where(
            db.product_versions.c.user_id == actor,
            db.product_versions.c.id == version_id)).scalar_one_or_none()
        if row is None:
            raise ApplicationError("External product version not found")
        source = connection.execute(sa.select(db.data_sources.c.kind, db.data_sources.c.evidence).where(
            db.data_sources.c.user_id == actor, db.data_sources.c.id == row)).mappings().one()
        if source["kind"] != "external_catalog":
            return
        exists = connection.execute(sa.select(db.product_confirmations.c.id).where(
            db.product_confirmations.c.user_id == actor,
            db.product_confirmations.c.product_version_id == version_id)).scalar_one_or_none()
        if exists is None:
            connection.execute(db.product_confirmations.insert().values(
                id=uuid4(), user_id=actor, product_version_id=version_id,
                confirmed_by_update_id=confirmed_by_update))


def _snapshot(values: dict[str, str | None], *, uncertainty: Decimal | None = None) -> NutritionSnapshot:
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
            central = Decimal(text)
            if uncertainty is None:
                lower = upper = None
            else:
                lower = decimal_text(central * (Decimal("1") - uncertainty))
                upper = decimal_text(central * (Decimal("1") + uncertainty))
            nutrients[name] = NutrientValue(value=text, lower=lower, upper=upper)
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
    snapshot = _snapshot(nutrition, uncertainty=ORDINARY_UNCERTAINTY)
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
    snapshot = _snapshot(nutrition, uncertainty=ORDINARY_UNCERTAINTY)
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
