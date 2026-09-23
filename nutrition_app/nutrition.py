"""Deterministic decimal calculations from pinned, compatible nutrition sources."""

from decimal import Decimal, ROUND_HALF_UP, localcontext

from nutrition_contracts.common import NutrientValue, NutritionSnapshot
from nutrition_contracts.results import CompleteTotal, DayNutrition, EmptyTotal, PartialTotal, UnknownTotal

from .errors import ApplicationError, NumericOverflow


NUTRIENTS = ("kcal", "protein_g", "fat_g", "carbs_g")
CALCULATION_VERSION = "decimal-components-v1"
RECIPE_CALCULATION_VERSION = "recipe-components-v1"
QUANTUM = Decimal("0.000001")
MAXIMUM = Decimal("999999999999.999999")


def decimal_text(value: Decimal) -> str:
    """Round a persisted value once; reject overflow instead of truncating it."""
    if not value.is_finite() or value < 0 or value > MAXIMUM:
        raise NumericOverflow("Nutrition value exceeds the supported numeric range")
    with localcontext() as context:
        context.prec = 64
        rounded = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    return format(rounded, "f").rstrip("0").rstrip(".") or "0"


def total(values) -> str:
    with localcontext() as context:
        context.prec = 64
        return decimal_text(sum((Decimal(value) for value in values), Decimal(0)))


def scale(snapshot: NutritionSnapshot, quantity: Decimal) -> NutritionSnapshot:
    if not quantity.is_finite() or quantity <= 0:
        raise ApplicationError("A positive, finite quantity is required")
    values = {}
    with localcontext() as context:
        context.prec = 64
        factor = quantity / Decimal(100)
        for name in NUTRIENTS:
            nutrient = getattr(snapshot, name)
            values[name] = None if nutrient is None else NutrientValue(
                value=decimal_text(Decimal(nutrient.value) * factor),
                lower=None if nutrient.lower is None else decimal_text(Decimal(nutrient.lower) * factor),
                upper=None if nutrient.upper is None else decimal_text(Decimal(nutrient.upper) * factor),
            )
    return NutritionSnapshot(**values)


def add_known(values: list[NutrientValue]) -> NutrientValue:
    all_bounded = all(value.lower is not None for value in values)
    return NutrientValue(value=total(value.value for value in values),
        lower=total(value.lower for value in values) if all_bounded else None,
        upper=total(value.upper for value in values) if all_bounded else None)


def entry_nutrition(snapshots: list[NutritionSnapshot]) -> NutritionSnapshot:
    """A partially known entry nutrient stays unknown; the day exposes subtotals."""
    result = {}
    for name in NUTRIENTS:
        known = [getattr(s, name) for s in snapshots if getattr(s, name) is not None]
        result[name] = add_known(known) if known and len(known) == len(snapshots) else None
    return NutritionSnapshot(**result)


def recipe_per_100_g(ingredients: list[tuple[NutritionSnapshot, Decimal]], finished_yield_g: Decimal) -> NutritionSnapshot:
    """Calculate recipe nutrition from per-100-g sources and normalized edible grams.

    ``finished_yield_g`` is a calculation basis, not a stored serving size. A
    caller may pass the sum of ingredient masses for the conditional
    ``ingredient_sum_no_evaporation`` policy, or a measured/approved cooked
    yield. Unknown source nutrients remain unknown rather than being inferred.
    Volume ingredients must be converted to grams by the caller using a pinned
    source density before entering this function.
    """
    if not ingredients:
        raise ApplicationError("A recipe requires at least one ingredient")
    if not finished_yield_g.is_finite() or finished_yield_g <= 0:
        raise ApplicationError("A positive, finite finished recipe yield is required")
    if any(not quantity.is_finite() or quantity <= 0 for _, quantity in ingredients):
        raise ApplicationError("Recipe ingredient quantities must be positive and finite")
    result = {}
    with localcontext() as context:
        context.prec = 64
        factor = Decimal(100) / finished_yield_g
        for name in NUTRIENTS:
            nutrients = [getattr(snapshot, name) for snapshot, _ in ingredients]
            if any(nutrient is None for nutrient in nutrients):
                result[name] = None
                continue
            values = [Decimal(nutrient.value) * quantity / Decimal(100)
                      for nutrient, (_, quantity) in zip(nutrients, ingredients)]
            all_bounded = all(nutrient.lower is not None for nutrient in nutrients)
            lower = upper = None
            if all_bounded:
                lower_values = [Decimal(nutrient.lower) * quantity / Decimal(100)
                                for nutrient, (_, quantity) in zip(nutrients, ingredients)]
                upper_values = [Decimal(nutrient.upper) * quantity / Decimal(100)
                                for nutrient, (_, quantity) in zip(nutrients, ingredients)]
                lower = decimal_text(sum(lower_values) * factor)
                upper = decimal_text(sum(upper_values) * factor)
            result[name] = NutrientValue(value=decimal_text(sum(values) * factor), lower=lower, upper=upper)
    return NutritionSnapshot(**result)


def day_nutrition(snapshots: list[NutritionSnapshot]) -> DayNutrition:
    result = {}
    for name in NUTRIENTS:
        known = [getattr(s, name) for s in snapshots if getattr(s, name) is not None]
        missing = len(snapshots) - len(known)
        if not snapshots:
            result[name] = EmptyTotal(kind="empty")
        elif not known:
            result[name] = UnknownTotal(kind="unknown", unknown_components=missing)
        elif missing:
            result[name] = PartialTotal(kind="partial", known_subtotal=total(v.value for v in known),
                                        known_components=len(known), unknown_components=missing)
        else:
            result[name] = CompleteTotal(kind="complete", amount=add_known(known), known_components=len(known))
    return DayNutrition(**result)


def to_columns(snapshot: NutritionSnapshot) -> dict:
    result = {}
    for name in NUTRIENTS:
        value = getattr(snapshot, name)
        result[name] = None if value is None else Decimal(value.value)
        result[name + "_lower"] = None if value is None or value.lower is None else Decimal(value.lower)
        result[name + "_upper"] = None if value is None or value.upper is None else Decimal(value.upper)
    return result


def from_columns(row) -> NutritionSnapshot:
    result = {}
    for name in NUTRIENTS:
        result[name] = None if row[name] is None else NutrientValue(
            value=decimal_text(row[name]),
            lower=None if row[name + "_lower"] is None else decimal_text(row[name + "_lower"]),
            upper=None if row[name + "_upper"] is None else decimal_text(row[name + "_upper"]),
        )
    return NutritionSnapshot(**result)
