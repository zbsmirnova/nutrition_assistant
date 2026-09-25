"""Russian food acknowledgments built solely from committed typed outcomes."""

import json

from nutrition_contracts.results import OutcomeEnvelope


def number(value: str) -> str:
    return value.replace(".", ",")


def nutrient(value) -> str:
    if value is None:
        return "неизвестно"
    result = number(value.value)
    if value.lower is not None:
        result += f" (оценка {number(value.lower)}–{number(value.upper)})"
    return result


def total(value) -> str:
    if value.kind == "complete":
        return nutrient(value.amount)
    if value.kind == "partial":
        return f"{number(value.known_subtotal)} — известная часть, есть пропуски"
    if value.kind == "unknown":
        return "неизвестно"
    return "нет записей"


def profile(snapshot, format_value):
    visible_fields = (("kcal", "Ккал"), ("protein_g", "Белки, г"))
    return "\n".join(f"{label}: {format_value(getattr(snapshot, key))}"
                     for key, label in visible_fields)


def render_food_result(payload: dict) -> str:
    result = OutcomeEnvelope.model_validate_json(json.dumps(payload)).result
    if (result.outcome != "applied" or len(result.food_entries) != 1
            or len(result.daily_summaries) != 1 or result.observations or result.recipe is not None):
        raise ValueError("Only M1 food outcomes are supported")
    entry, day = result.food_entries[0], result.daily_summaries[0]
    if entry.change not in {"added", "corrected"}:
        raise ValueError("This food change cannot be rendered as a saved result")
    # Plain text has no parse mode. Bound a user-supplied label independently so
    # even the longest allowed source cannot crowd out nutrition/coverage.
    name = " ".join(entry.description.split())[:160]
    if len(" ".join(entry.description.split())) > 160:
        name += "…"
    estimate_note = "\nКоличество отмечено по вашему предположению." if entry.estimated else ""
    verb = "Записано" if entry.change == "added" else "Исправлено"
    text = (f"{verb}: {name}{estimate_note}\n{profile(entry.nutrition, nutrient)}\n\n"
            "Итого за сегодня:\n"
            f"{profile(day.nutrition, total)}")
    if len(text.encode("utf-16-le")) // 2 > 4000:
        raise ValueError("Response exceeds the safe message limit")
    return text


def render_observation_result(payload: dict) -> str:
    result = OutcomeEnvelope.model_validate_json(json.dumps(payload)).result
    if result.outcome == "no_change" and getattr(result, "reason", None) == "same_value":
        return "Это значение уже записано на этот день. Ничего не изменилось."
    if (result.outcome != "applied" or len(result.observations) != 1
            or result.food_entries or result.recipe is not None or result.daily_summaries):
        raise ValueError("Only daily observation outcomes are supported")
    observation = result.observations[0]
    day = observation.effective_date.strftime("%d.%m.%Y")
    if observation.kind == "daily_weight":
        return f"Вес за сегодня записан: {number(observation.value_kg)} кг."
    return f"Записано шагов за {day}: {observation.steps}."


def render_day_result(payload: dict) -> str:
    result = OutcomeEnvelope.model_validate_json(json.dumps(payload)).result
    if result.outcome != "day_summary":
        raise ValueError("Not a day summary result")
    # Readback intentionally exposes only the MVP-facing calorie and protein
    # totals; fat and carbohydrates remain persisted for later views.
    return f"Итого за сегодня:\n{profile(result.summary.nutrition, total)}"


def render_clarification_result(payload: dict) -> str:
    result = OutcomeEnvelope.model_validate_json(json.dumps(payload)).result
    if result.outcome != "needs_clarification":
        raise ValueError("Not a clarification result")
    return "\n".join(question.prompt for question in result.questions)


def render_result(payload: dict) -> str:
    """Render any supported committed outcome into a Russian confirmation."""
    try:
        return render_clarification_result(payload)
    except ValueError:
        pass
    try:
        return render_observation_result(payload)
    except ValueError:
        pass
    try:
        return render_day_result(payload)
    except ValueError:
        return render_food_result(payload)
