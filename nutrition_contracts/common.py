"""Shared strict wire types. Quantities use decimal strings, never JSON floats."""

from decimal import Decimal
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, AfterValidator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


Text = Annotated[str, StringConstraints(min_length=1, max_length=16000, pattern=r"\S")]
Name = Annotated[str, StringConstraints(min_length=1, max_length=256, pattern=r"\S")]
# Some JSON Schema regex engines let `$` match before a trailing newline.
# The portable exclusion keeps their accepted wire values aligned with Python.
DecimalText = Annotated[
    str, StringConstraints(pattern=r"^(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,6})?$"),
    Field(json_schema_extra={"not": {"pattern": r"\s"}}),
]
PositiveDecimal = Annotated[str, StringConstraints(
    pattern=(r"^(?:[1-9][0-9]{0,11}(?:\.[0-9]{1,6})?|0\."
             r"(?:[1-9][0-9]{0,5}|0[1-9][0-9]{0,4}|00[1-9][0-9]{0,3}|"
             r"000[1-9][0-9]{0,2}|0000[1-9][0-9]?|00000[1-9]))$")
), Field(json_schema_extra={"not": {"pattern": r"\s"}})]
Count = Annotated[int, Field(ge=0, le=9223372036854775807)]
PositiveCount = Annotated[int, Field(gt=0, le=9223372036854775807)]
ActionId = Annotated[str, StringConstraints(pattern=r"^a[1-9][0-9]*$"), Field(json_schema_extra={"not": {"pattern": r"\s"}})]
CandidateToken = Annotated[str, StringConstraints(pattern=r"^c[1-9][0-9]*$"), Field(json_schema_extra={"not": {"pattern": r"\s"}})]
QuestionToken = Annotated[str, StringConstraints(pattern=r"^q[1-9][0-9]*$"), Field(json_schema_extra={"not": {"pattern": r"\s"}})]
Meal = Literal["breakfast", "lunch", "dinner", "snack", "unspecified"]
Unit = Literal["g", "kg", "ml", "l", "piece"]
WeightBasis = Literal["raw", "cooked", "as_sold"]


def _time_zone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("must be a recognized IANA time zone") from exc
    return value


TimeZoneName = Annotated[str, StringConstraints(min_length=1, max_length=128), AfterValidator(_time_zone)]


class QuantityMention(Contract):
    """Extracted amount; NULL means not supplied, not zero or permission to guess."""

    amount: PositiveDecimal | None
    unit: Unit | None


class SuppliedNutrition(Contract):
    """Only values explicitly supplied by the user, at a separately specified basis."""

    kcal: DecimalText | None
    protein_g: DecimalText | None
    fat_g: DecimalText | None
    carbs_g: DecimalText | None


class NutrientValue(Contract):
    value: DecimalText
    lower: DecimalText | None
    upper: DecimalText | None

    @model_validator(mode="after")
    def ordered_bounds(self) -> Self:
        if (self.lower is None) != (self.upper is None):
            raise ValueError("provide both bounds or neither")
        if self.lower is not None and not Decimal(self.lower) <= Decimal(self.value) <= Decimal(self.upper):
            raise ValueError("bounds must enclose the central value")
        return self


class NutritionSnapshot(Contract):
    kcal: NutrientValue | None
    protein_g: NutrientValue | None
    fat_g: NutrientValue | None
    carbs_g: NutrientValue | None


class CandidateReference(Contract):
    kind: Literal["candidate"]
    candidate_ref: CandidateToken
    candidate_kind: Literal["product", "recipe", "entry", "pending", "estimate"]


class FoodCandidate(CandidateReference):
    candidate_kind: Literal["product", "recipe"]


class EntryCandidate(CandidateReference):
    candidate_kind: Literal["entry"]


class RecipeCandidate(CandidateReference):
    candidate_kind: Literal["recipe"]


class ProductCandidate(CandidateReference):
    candidate_kind: Literal["product"]


class PendingCandidate(CandidateReference):
    candidate_kind: Literal["pending"]


class NamedFood(Contract):
    kind: Literal["name"]
    name: Name


class ActionResultReference(Contract):
    kind: Literal["action_result"]
    action_id: ActionId


FoodReference = Annotated[FoodCandidate | NamedFood | ActionResultReference, Field(discriminator="kind")]


class ReplyTarget(Contract):
    kind: Literal["reply"]


class DescribedTarget(Contract):
    kind: Literal["description"]
    description: Text


EntryTarget = Annotated[EntryCandidate | ReplyTarget | DescribedTarget, Field(discriminator="kind")]
RecipeTarget = Annotated[RecipeCandidate | DescribedTarget, Field(discriminator="kind")]
ProductTarget = Annotated[ProductCandidate | DescribedTarget, Field(discriminator="kind")]


class DateHint(Contract):
    """Original date words. Backend resolves relative dates against the source input."""

    text: Text | None


class IngredientMention(Contract):
    food: Annotated[ProductCandidate | NamedFood, Field(discriminator="kind")]
    quantity: QuantityMention
    weight_basis: WeightBasis | None


class UnresolvedField(Contract):
    path: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    reason: Literal["missing", "ambiguous", "conflicting"]


class SourceQuantity(Contract):
    amount: PositiveDecimal
    unit: Unit


class Mass(Contract):
    kind: Literal["mass"]
    edible_g: PositiveDecimal
    gross_g: PositiveDecimal | None
    inedible_g: DecimalText | None
    weight_basis: WeightBasis

    @model_validator(mode="after")
    def consistent_mass(self) -> Self:
        if self.gross_g is not None:
            if Decimal(self.edible_g) > Decimal(self.gross_g):
                raise ValueError("edible weight exceeds gross weight")
            if self.inedible_g is not None and Decimal(self.edible_g) + Decimal(self.inedible_g) != Decimal(self.gross_g):
                raise ValueError("gross weight must equal edible plus inedible weight")
        return self


class Volume(Contract):
    kind: Literal["volume"]
    ml: PositiveDecimal
    weight_basis: WeightBasis


NormalizedQuantity = Annotated[Mass | Volume, Field(discriminator="kind")]
