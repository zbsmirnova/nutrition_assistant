"""Provider-neutral proposals and deliberately bounded single-food resolution.

This is not a Russian-language model. Text checks guard explicit evidence; model
intent accuracy still requires separate evaluation before real-message use.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
import json
import re
from typing import Protocol
from uuid import UUID

from nutrition_contracts.commands import CommandEnvelope
from nutrition_contracts.parser import (AddFood, AnswerClarification, NonLogging, ParserOutput,
                                         NutritionAnswer, validate_parser_context)

from .errors import ApplicationError
from .service import digest, operation_id_for


CONTEXT_VERSION = "single-food-context-v2"
RESOLVER_VERSION = "single-food-resolver-v5"
MAX_CANDIDATES = 64


@dataclass(frozen=True)
class ParserRequest:
    source_text: str = field(repr=False)
    local_date: str
    time_zone: str
    candidates: tuple[dict, ...] = field(repr=False)
    pending_candidates: tuple[dict, ...] = field(default_factory=tuple, repr=False)
    pending_questions: dict[str, dict[str, str]] = field(default_factory=dict, repr=False)
    has_reply: bool = False


class Parser(Protocol):
    version: str

    def parse(self, request: ParserRequest) -> str: ...


class ParserUnavailable(ApplicationError):
    code = "parser_unavailable"

    def __init__(self, message="Parser unavailable", *, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after if type(retry_after) is int and 0 <= retry_after <= 86400 else None


class ParserRejected(ApplicationError):
    """A permanent provider/configuration/proposal failure, never silently retried."""
    code = "parser_rejected"


class SyntheticParser:
    """Explicit controlled response, bound to exact source text and catalog names.

    It never reads credentials or calls a model. The fixture fingerprint makes
    changing responses across a resumed interpretation visible.
    """

    def __init__(self, fixture: dict):
        if (not isinstance(fixture, dict) or set(fixture) != {"source_text", "candidate_names", "output"}
                or not isinstance(fixture["source_text"], str)
                or not isinstance(fixture["candidate_names"], list)
                or not all(isinstance(n, str) for n in fixture["candidate_names"])
                or not isinstance(fixture["output"], dict)):
            raise ApplicationError("Invalid synthetic parser fixture")
        self._fixture = json.loads(json.dumps(fixture))
        self.version = "synthetic:" + digest(self._fixture)

    def parse(self, request: ParserRequest) -> str:
        if (request.source_text != self._fixture["source_text"] or
                [c["name"] for c in request.candidates] != self._fixture["candidate_names"]):
            raise ParserUnavailable("Synthetic fixture does not match the input context")
        return json.dumps(self._fixture["output"], ensure_ascii=False)


def parser_request(context: dict) -> ParserRequest:
    """The adapter receives no actor, Telegram identity, or database IDs."""
    public = tuple({k: c[k] for k in ("ref", "name", "nutrition_basis", "weight_basis",
                                     "food_kind", "declared_fat_percent")}
                   for c in context["candidates"])
    pending = tuple({k: c[k] for k in ("ref", "name", "nutrition_basis", "weight_basis",
                                       "food_kind", "declared_fat_percent")}
                    for c in context.get("pending_candidates", ()))
    return ParserRequest(source_text=context["source_text"], local_date=context["local_date"],
                         time_zone=context["time_zone"], candidates=public,
                         pending_candidates=pending,
                         pending_questions=context.get("pending_questions", {}),
                         has_reply=context.get("has_reply", False))


@dataclass(frozen=True)
class Resolution:
    status: str
    reason: str
    command: CommandEnvelope | None = None
    pending_food_date: date | None = None
    pending_questions: dict[str, dict[str, str]] | None = None
    pending_position: int | None = None
    command_position: int | None = None


def normalized(text: str) -> str:
    return " ".join(text.casefold().replace("ё", "е").split())


DATE_WORDS = re.compile(r"\b(?:сегодня|вчера|позавчера|завтра|послезавтра|today|yesterday|tomorrow|"
                        r"назад|прошл\w*|накануне|раньше|ago|last|"
                        r"понедельник\w*|вторник\w*|сред[ауеы]|четверг\w*|пятниц\w*|суббот\w*|воскресень\w*|"
                        r"январ\w*|феврал\w*|март\w*|апрел\w*|ма[йяе]|июн\w*|июл\w*|август\w*|"
                        r"сентябр\w*|октябр\w*|ноябр\w*|декабр\w*)\b|"
                        r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b|\b[0-9]{1,2}[./][0-9]{1,2}(?:[./][0-9]{2,4})?\b", re.I)


def effective_date(context: dict, hint: str | None) -> date | None:
    source = normalized(context["source_text"])
    # Dot-decimal masses and label percentages are not short date expressions.
    numeric_spans = [(m.start(), m.end()) for pattern in (QUANTITY, PERCENT) for m in pattern.finditer(source)]
    markers = [m.group() for m in DATE_WORDS.finditer(source)
               if not any(start <= m.start() and m.end() <= end for start, end in numeric_spans)]
    original = date.fromisoformat(context["local_date"])
    # The source-message date is authoritative when the message contains no
    # date evidence. A model hint cannot invent a date that the user did not
    # write; this also makes the default independent of model formatting.
    if not markers:
        return original
    if hint is None:
        return None
    token = normalized(hint)
    if token not in source or len(markers) != 1 or markers[0] != token:
        return None
    if token in {"сегодня", "today"}:
        return original
    if token in {"вчера", "yesterday"}:
        return original - timedelta(days=1)
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", token):
        try:
            return date.fromisoformat(token)
        except ValueError:
            pass
    return None


QUANTITY = re.compile(r"(?<![\w.,+\-−])[0-9]+(?:[.,][0-9]+)?\s*(?:килограмм(?:а|ов)?|грамм(?:а|ов)?|"
                      r"миллилитр(?:а|ов)?|литр(?:а|ов)?|кг|мл|kg|ml|г|g|л|l)(?!\w)", re.I)
AMOUNT_UNIT = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*(.*)")
UNITS = {"г": "g", "грамм": "g", "грамма": "g", "граммов": "g", "g": "g",
         "кг": "kg", "килограмм": "kg", "килограмма": "kg", "килограммов": "kg", "kg": "kg",
         "мл": "ml", "миллилитр": "ml", "миллилитра": "ml", "миллилитров": "ml", "ml": "ml",
         "л": "l", "литр": "l", "литра": "l", "литров": "l", "l": "l"}
PERCENT = re.compile(r"(?<![\w.,+\-−])([0-9]+(?:[.,][0-9]+)?)\s*%")
DAIRY_WORD = re.compile(r"\b(?:творог\w*|молок\w*|кефир\w*|йогурт\w*|сливк\w*|сметан\w*|"
                        r"ряженк\w*|сыр\w*|milk|kefir|yog[hu]urt|cream|cheese|quark|curd)\b", re.I)
NON_CONSUMPTION = re.compile(r"\b(?:планир\w*|собираюсь|буду|хочу|не|не\s+ел\w*|"
                             r"калорий|рецепт\w*|сохран\w*|исправ\w*|вместо|"
                             r"или|либо|or|plan\w*|tomorrow|recipe|instead|not)\b|[?]", re.I)
APPROXIMATE = re.compile(r"\b(?:примерно|около|приблизительно|где-то|roughly|about|approximately)\b|[~≈]", re.I)
RAW_WORD = re.compile(r"\b(?:сыр(?:ой|ая|ое|ые|ого|ую|ых|ом)|raw|uncooked)\b", re.I)
COOKED_WORD = re.compile(r"\b(?:варен\w*|отварн\w*|жарен\w*|запеченн\w*|приготовлен\w*|готов(?:ый|ая|ое|ые|ого|ую|ых|ом)|"
                         r"cooked|boiled|fried|baked)\b", re.I)


def identity_words(text):
    """Conservative lexical identity evidence, not synonym/semantic retrieval.

    Strip common noun endings to admit supplied Russian catalog names in simple
    inflections. Brand letters/numbers and all other distinguishing words must
    still occur in the actual input. Broader aliases require later resolution.
    """
    words = re.findall(r"[a-zа-я]+|[0-9]+", normalized(PERCENT.sub("", text)))
    result = set()
    for word in words:
        if len(word) > 4 and re.fullmatch(r"[а-я]+", word):
            word = re.sub(r"(?:ами|ями|ого|ому|ой|ая|ую|ые|ым|ом|ов|ам|а|я|ы|и|у|е|о)$", "", word)
        result.add(word)
    return result


def resolve(actor: UUID, origin: UUID, context: dict, output: ParserOutput) -> Resolution:
    candidate_kinds = {c["ref"]: "product" for c in context["candidates"]}
    candidate_kinds.update({c["ref"]: "pending" for c in context.get("pending_candidates", ())})
    validate_parser_context(output, candidate_kinds, context.get("pending_questions", {}),
                            source_text=context["source_text"], has_reply=context["has_reply"])
    if len(output.actions) != 1:
        return Resolution("unsupported", "multiple_actions")
    action = output.actions[0]
    if isinstance(action, NonLogging):
        status = {"ambiguous_intent": "unresolved", "unsupported": "unsupported"}.get(action.reason, "non_logging")
        return Resolution(status, action.reason)
    if isinstance(action, AnswerClarification):
        pending = context.get("pending")
        if pending is None or action.pending is None:
            return Resolution("unresolved", "clarification_context_missing")
        if action.pending.candidate_ref not in context.get("pending_questions", {}):
            return Resolution("unresolved", "clarification_context_missing")
        original_output = ParserOutput.model_validate(pending["proposal"])
        pending_position = pending.get("position", 0)
        if not 0 <= pending_position < len(original_output.actions):
            return Resolution("unsupported", "pending_action_not_implemented")
        original_action = original_output.actions[pending_position]
        if not isinstance(original_action, AddFood):
            return Resolution("unsupported", "pending_action_not_implemented")
        original = ParserOutput(schema_version=original_output.schema_version, actions=[original_action])
        # The answer is evidence for the original action. Backend resolution
        # re-runs against the original message plus the answer, preserving the
        # original local date and operation identity.
        answer_text = context["source_text"]
        merged = dict(pending["context"])
        merged["source_text"] = original_action.evidence + "\n" + answer_text
        merged["has_reply"] = False
        merged["forwarded"] = False
        merged["pending_questions"] = {}
        merged["pending_candidates"] = []
        merged["pending_identity_confirmed"] = True
        merged["operation_position"] = pending_position
        merged["evidence_update_ids"] = [UUID(pending["origin_update_id"]), origin]
        merged["pending_action_id"] = UUID(pending["job_id"])
        nutrition_answers = [answer.value for answer in action.answers if isinstance(answer.value, NutritionAnswer)]
        if not nutrition_answers or nutrition_answers[0].supplied_nutrition.fat_g is None:
            return Resolution("unresolved", "clarification_answer_incomplete",
                              pending_food_date=date.fromisoformat(pending["context"]["local_date"]),
                              pending_questions=context["pending_questions"])
        return resolve(actor, UUID(pending["origin_update_id"]), merged, original)
    if not isinstance(action, AddFood):
        return Resolution("unsupported", "action_not_implemented")
    target_date = effective_date(context, action.date_hint.text)
    pending_ref = action.food.candidate_ref if action.food.kind == "candidate" else None

    def defer(reason):
        questions = None
        if reason == "dairy_fat_missing" and pending_ref is not None:
            questions = {pending_ref: {"q1": "nutrition"}}
        return Resolution("unresolved", reason, pending_food_date=target_date, pending_questions=questions)

    if action.depends_on or action.unresolved:
        return defer("proposal_unresolved")
    if context["has_reply"] or context["forwarded"]:
        return defer("conversation_context_required")
    if NON_CONSUMPTION.search(context["source_text"]):
        return defer("consumption_evidence_conflict")
    if target_date is None:
        return defer("date_unresolved")
    candidates = context["candidates"]
    if action.food.kind == "candidate":
        matching = [c for c in candidates if c["ref"] == action.food.candidate_ref]
    elif action.food.kind == "name":
        matching = [c for c in candidates if normalized(c["name"]) == normalized(action.food.name)]
    else:
        return Resolution("unsupported", "dependent_food_source")
    if len(matching) != 1:
        return defer("product_unresolved")
    pending_ref = matching[0]["ref"]
    product = matching[0]
    # Duplicate indistinguishable names are ambiguity even if the model picked a token.
    if sum(normalized(c["name"]) == normalized(product["name"]) for c in candidates) != 1:
        return defer("product_ambiguous")
    if product["food_kind"] is None:
        return defer("catalog_identity_unclassified")
    text = context["source_text"]
    dairy = product["food_kind"] == "dairy" or bool(DAIRY_WORD.search(product["name"]))
    if dairy:
        label_fat = product["declared_fat_percent"]
        percentages = [Decimal(m.group(1).replace(",", ".")) for m in PERCENT.finditer(text)]
        if text.count("%") != len(percentages):
            return defer("dairy_fat_conflict")
        if percentages:
            if label_fat is None:
                return defer("catalog_fat_unknown")
            if len(percentages) != 1 or percentages[0] != Decimal(label_fat):
                return defer("dairy_fat_conflict")
        else:
            # A generic name such as "творог" is never an exact branded identity.
            # An explicit full catalog name with a distinguishing word is sufficient.
            distinctive = PERCENT.sub("", DAIRY_WORD.sub("", product["name"]))
            if (not re.search(r"[a-zа-я]{2,}", distinctive, re.I)
                    or normalized(product["name"]) not in normalized(text)):
                return defer("dairy_fat_missing")
    if (not context.get("pending_identity_confirmed")
            and not identity_words(product["name"]).issubset(identity_words(text))):
        return defer("product_evidence_conflict")
    folded = normalized(text)
    if ((RAW_WORD.search(folded) and product["weight_basis"] != "raw") or
            (COOKED_WORD.search(folded) and product["weight_basis"] != "cooked")):
        return defer("weight_basis_evidence_conflict")
    quantity = action.quantity
    matches = list(QUANTITY.finditer(text))
    if quantity.amount is None or quantity.unit is None or len(matches) != 1:
        return defer("quantity_unresolved")
    prefix = text[:matches[0].start()]
    if (APPROXIMATE.search(text)
            or re.search(r"[0-9]\s*(?:[-–—−×*x]|до|to)\s*$", prefix, re.I)
            or re.search(r"(?:[<>≤≥±]|\b(?:до|от|менее|более|меньше|больше|минимум|максимум|"
                         r"up to|at least|at most|less than|more than|under|over))\s*$", prefix, re.I)):
        return defer("quantity_not_exact")
    lexical = AMOUNT_UNIT.fullmatch(matches[0].group())
    if (Decimal(lexical.group(1).replace(",", ".")) != Decimal(quantity.amount)
            or UNITS[lexical.group(2).casefold()] != quantity.unit):
        return defer("quantity_evidence_conflict")
    if action.weight_basis is None or action.weight_basis != product["weight_basis"]:
        return defer("weight_basis_unresolved")
    if quantity.unit not in {"g", "ml"}:
        # Unit conversion can be added deliberately; never let it happen implicitly.
        return defer("unit_conversion_required")
    if (quantity.unit == "g") != (product["nutrition_basis"] == "per_100_g"):
        return defer("unit_basis_mismatch")
    amount = quantity.amount
    normalized_quantity = ({"kind": "mass", "edible_g": amount, "gross_g": None, "inedible_g": None,
                            "weight_basis": product["weight_basis"]} if quantity.unit == "g" else
                           {"kind": "volume", "ml": amount, "weight_basis": product["weight_basis"]})
    evidence_ids = context.get("evidence_update_ids", [origin])
    pending_action_id = context.get("pending_action_id")
    payload = {"schema_version": "1.0", "user_id": str(actor),
               "operation_id": str(operation_id_for(origin, context.get("operation_position", 0))),
               "context_revision": context["context_revision"],
               "source": {"origin_update_id": str(origin), "evidence_update_ids": [str(item) for item in evidence_ids],
                          "pending_action_id": None if pending_action_id is None else str(pending_action_id)},
               "command": {"kind": "add_consumed_food", "food": {
                   "effective_date": target_date.isoformat(), "time_zone": context["time_zone"], "meal": action.meal,
                   "description": product["name"], "components": [{"kind": "product", "description": product["name"],
                       "product_version_id": product["version_id"], "quantity": normalized_quantity}]}}}
    return Resolution("ready", "command_prepared", CommandEnvelope.model_validate_json(json.dumps(payload)),
                      command_position=context.get("operation_position", 0))


def resolve_actions(actor: UUID, origin: UUID, context: dict, output: ParserOutput) -> list[Resolution]:
    """Resolve independent actions against their own evidence excerpts.

    The first partial-saving slice deliberately accepts at most one ready and
    one unresolved add-food action. Keeping this helper separate preserves the
    single-action resolver as the trusted backend primitive.
    """
    results = []
    for position, action in enumerate(output.actions):
        action_context = dict(context)
        action_context["source_text"] = action.evidence
        action_context["operation_position"] = position
        single = ParserOutput(schema_version=output.schema_version, actions=[action])
        results.append(resolve(actor, origin, action_context, single))
    return results
