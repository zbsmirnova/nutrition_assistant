"""Batch interpretation-layer evaluation for hypothesis #1 (Russian food messages).

Runs each authored case in interpretation_v1.json through a parser and scores the
model's raw ParserOutput against the draft rubric. It never opens the database and
never resolves/persists anything; it measures interpretation quality only.

Parsers:
  --parser nebius  (default) uses NEBIUS_API_KEY and NUTRITION_LLM_MODEL from the
                   environment. This performs one live model call per case.
  --parser stub    uses an offline canned parser to prove the instrument end-to-end
                   without any credentials. Stub outputs are deliberately imperfect
                   so the scorecard exercises both passes and failures.

Usage:
  .venv/bin/python -m evals.run_interpretation_eval --parser stub
  SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python -m evals.run_interpretation_eval --parser nebius
  .venv/bin/python -m evals.run_interpretation_eval --parser stub --json
  .venv/bin/python -m evals.run_interpretation_eval --render-json /tmp/report.json
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

from nutrition_contracts.parser import ParserOutput

from nutrition_app.interpretation import ParserRejected, ParserUnavailable, parser_request

CASES = Path(__file__).with_name("interpretation_v1.json")


# --------------------------------------------------------------------------- parsers


def build_nebius_parser(prompt_path: str | None = None):
    from nutrition_app.nebius import NebiusConfig, NebiusParser

    prompt = Path(prompt_path).read_text(encoding="utf-8") if prompt_path else None
    return NebiusParser(NebiusConfig.from_environment(), prompt=prompt)


class StubParser:
    """Offline canned parser keyed by case id, for proving the instrument runs.

    Each spec is a list of add_food items (ref-or-name, amount, unresolved-paths)
    plus an optional flag to emit extra/ambiguous behavior, so the scorecard shows a
    realistic mix rather than a perfect score.
    """

    version = "stub:interpretation-eval-v1"

    SPECS = {
        # Mostly right: four components, source quantities, coffee left out (gap).
        "INTAKE-001": [("c1", "115", []), ("c2", "115", []), ("c3", "52", []), ("c4", "7", []), ("c5", "45", [])],
        # Clean single product: correct.
        "INTAKE-002": [("c1", "10", [])],
        # Lunch: extracts items and asks about the chicken (correct clarification).
        "INTAKE-003": [("c1", "120", ["quantity"]), ("c2", "100", []), ("c3", "100", [])],
        # Peach + physalis; physalis quantity left unresolved (no grams).
        "INTAKE-004": [("c1", "100", []), ("c2", None, ["quantity"])],
        # Breakfast partial: pate ambiguous -> unresolved food (correct clarification).
        "INTAKE-005": [("c1", "115", []), ("c2", "43", []), ("c3", "3", []), ("name:паштет", "40", ["food"])],
        # Spelling tolerance: matches брецель. correct.
        "INTAKE-006": [("c1", "30", [])],
        # History reference resolved to the supplied candidate. correct.
        "INTAKE-007": [("c1", "20", [])],
        # Potato+sweet potato total + explicit oil; DELIBERATE FAULT: adds a 4th
        # hidden oil item to exercise the max_add_food guard failing.
        "INTAKE-008": [("c1", "120", []), ("c2", "120", []), ("c3", "3", []), ("name:масло скрытое", "5", [])],
        # Chicken with bone: DELIBERATE FAULT: saves 150 g with no clarification, to
        # exercise a missed-clarification failure.
        "INTAKE-009": [("c1", "150", [])],
    }

    def __init__(self, cases):
        self._by_text = {case["source_text"]: case for case in cases}

    def parse(self, request) -> str:
        case = self._by_text[request.source_text]
        recipe_refs = {r["ref"] for r in case.get("recipes", [])}
        spec = self.SPECS[case["id"]]
        actions = []
        for index, (ref, amount, unresolved) in enumerate(spec, start=1):
            if ref.startswith("name:"):
                food = {"kind": "name", "name": ref[len("name:"):]}
            else:
                food = {"kind": "candidate", "candidate_kind": "recipe" if ref in recipe_refs else "product",
                        "candidate_ref": ref}
            actions.append({
                "kind": "add_food", "action_id": f"a{index}", "evidence": case["source_text"],
                "depends_on": [], "unresolved": [{"path": path, "reason": "missing"} for path in unresolved],
                "food": food, "quantity": {"amount": amount, "unit": "g" if amount else None},
                "weight_basis": "as_sold", "date_hint": {"text": None}, "meal": "unspecified"})
        return json.dumps({"schema_version": "1.0", "actions": actions}, ensure_ascii=False)


# --------------------------------------------------------------------------- scoring


def _decimal_equal(a, b) -> bool:
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except (InvalidOperation, TypeError):
        return False


def _evidence_ok(action, source_cf: str) -> bool:
    """Evidence must be a real, non-trivial excerpt of the source (not a 1-char span)."""
    ev = getattr(action, "evidence", None)
    return isinstance(ev, str) and len(ev.strip()) >= 3 and ev.strip().casefold() in source_cf


def _date_hint_ok(action, expect: dict, source_cf: str) -> bool:
    """date_hint.text must be null unless the case declares real date evidence, and must
    be quoted from the source. Catches invented hints like "2" that no rule should emit."""
    dh = getattr(action, "date_hint", None)
    if dh is None or getattr(dh, "text", None) is None:
        return True
    if expect.get("date_hint") != "present":
        return False
    return dh.text.strip().casefold() in source_cf


def score_case(case: dict, output: ParserOutput) -> dict:
    expect = case["expect"]
    source_cf = case["source_text"].casefold()
    actions = output.actions
    add_food = [a for a in actions if a.kind == "add_food"]
    amounts = [a.quantity.amount for a in add_food if a.quantity and a.quantity.amount is not None]
    selected = {a.food.candidate_ref for a in add_food
                if getattr(a.food, "kind", None) == "candidate"}
    has_clar = any(a.unresolved for a in actions)
    clar_paths = {item.path.split(".")[0] for a in actions for item in a.unresolved}

    checks: dict[str, bool] = {}
    checks["consumed"] = (len(add_food) > 0) == bool(expect["consumed"])

    # Per-action quality gates: an action with a 1-char evidence span or an invented
    # date hint is broken even when the JSON validates and the counts look right.
    checks["evidence_valid"] = all(_evidence_ok(a, source_cf) for a in actions)
    checks["date_hint_valid"] = all(_date_hint_ok(a, expect, source_cf) for a in actions)

    lo, hi = expect["add_food_range"]
    checks["add_food_count"] = lo <= len(add_food) <= hi

    mode = expect.get("clarification", "optional")
    if mode == "required":
        checks["clarification"] = has_clar
        if expect.get("clarification_paths_any"):
            checks["clarification_paths"] = bool(clar_paths & set(expect["clarification_paths_any"]))
    elif mode == "forbidden":
        checks["clarification"] = not has_clar

    if expect.get("quantities_any"):
        checks["quantities"] = all(
            any(_decimal_equal(want, got) for got in amounts) for want in expect["quantities_any"])

    if expect.get("select_refs_any"):
        allowed = set(expect["select_refs_any"])
        # Must select at least one expected candidate AND select nothing outside the
        # allowed set (the old check ignored wrong/extra candidate picks).
        checks["candidate_selection"] = bool(selected) and selected <= allowed

    if "max_add_food" in expect:
        checks["max_add_food"] = len(add_food) <= expect["max_add_food"]

    return {
        "checks": checks,
        "passed": all(checks.values()),
        "n_add_food": len(add_food),
        "clarification_mode": mode,
        "clarification_raised": has_clar,
        "clarification_paths": sorted(clar_paths),
        "selected_refs": sorted(selected),
    }


# --------------------------------------------------------------------------- driver


def run(parser_name: str, only: str | None, prompt_path: str | None = None) -> dict:
    corpus = json.loads(CASES.read_text(encoding="utf-8"))
    cases = [c for c in corpus["cases"] if only is None or c["id"] == only]
    parser = StubParser(cases) if parser_name == "stub" else build_nebius_parser(prompt_path)

    results = []
    for case in cases:
        context = {"source_text": case["source_text"], "local_date": case["local_date"],
                   "time_zone": case["time_zone"], "candidates": case["candidates"],
                   "recipes": case.get("recipes", []), "entries": case.get("entries", [])}
        entry = {"id": case["id"], "known_gaps": len(case.get("known_gaps", []))}
        try:
            raw = parser.parse(parser_request(context))
            output = ParserOutput.model_validate_json(raw)
        except (ParserRejected, ParserUnavailable) as exc:
            entry.update(error=type(exc).__name__, message=str(exc), passed=False, checks={})
        except Exception as exc:  # noqa: BLE001 - eval must not crash on one bad case
            entry.update(error=type(exc).__name__, message=str(exc), passed=False, checks={})
        else:
            entry.update(score_case(case, output))
            # Raw proposal captured for diagnosis (which fields the model missed/split).
            entry["output"] = output.model_dump(mode="json")
        results.append(entry)

    return {"parser": parser.version, "prompt": prompt_path or "production (nebius_prompt.txt)",
            "thresholds": corpus["draft_thresholds"], "results": results,
            "summary": summarize(results)}


def summarize(results: list[dict]) -> dict:
    scored = [r for r in results if "checks" in r and r["checks"]]
    n = len(results)
    passed = sum(1 for r in results if r.get("passed"))

    def rate(check: str) -> str:
        applicable = [r for r in scored if check in r["checks"]]
        if not applicable:
            return "n/a"
        return f"{sum(1 for r in applicable if r['checks'][check]) / len(applicable):.2f} ({len(applicable)})"

    def clar_rate(mode: str, want_raised: bool) -> str:
        cases = [r for r in scored if r.get("clarification_mode") == mode]
        if not cases:
            return "n/a"
        return f"{sum(1 for r in cases if r['clarification_raised'] == want_raised) / len(cases):.2f} ({len(cases)})"

    return {
        "cases": n,
        "case_pass_rate": f"{passed / n:.2f}" if n else "n/a",
        "consumed": rate("consumed"),
        "add_food_count": rate("add_food_count"),
        "evidence_valid": rate("evidence_valid"),
        "date_hint_valid": rate("date_hint_valid"),
        # Blended clarification metric hides the failure mode; recall/specificity separate it.
        "clarification_accuracy": rate("clarification"),
        "clarification_recall": clar_rate("required", True),
        "clarification_specificity": clar_rate("forbidden", False),
        "quantity_extraction": rate("quantities"),
        "candidate_selection": rate("candidate_selection"),
        "max_add_food_respected": rate("max_add_food"),
        "errors": sum(1 for r in results if r.get("error")),
    }


def format_report(report: dict) -> str:
    lines = [f"Parser: {report['parser']}", f"Prompt: {report['prompt']}", ""]
    lines.append(f"{'case':<12} {'pass':<5} {'#food':<6} {'clar?':<6} checks / notes")
    lines.append("-" * 78)
    for r in report["results"]:
        if r.get("error"):
            lines.append(f"{r['id']:<12} {'ERR':<5} {'-':<6} {'-':<6} {r['error']}: {r.get('message', '')[:44]}")
            continue
        failed = [k for k, v in r["checks"].items() if not v]
        note = "OK" if not failed else "FAIL: " + ",".join(failed)
        gaps = f" [gaps:{r['known_gaps']}]" if r["known_gaps"] else ""
        lines.append(f"{r['id']:<12} {('yes' if r['passed'] else 'no'):<5} "
                     f"{r['n_add_food']:<6} {('yes' if r['clarification_raised'] else 'no'):<6} {note}{gaps}")
    s = report["summary"]
    lines += ["", "Aggregate (rate (n)):",
              f"  case pass rate        {s['case_pass_rate']}",
              f"  consumed intent       {s['consumed']}",
              f"  add_food count        {s['add_food_count']}",
              f"  evidence spans valid  {s['evidence_valid']}",
              f"  date_hint valid       {s['date_hint_valid']}",
              f"  clarification recall  {s['clarification_recall']}   (required cases that asked)",
              f"  clarification specif. {s['clarification_specificity']}   (clean cases kept silent)",
              f"  quantity extraction   {s['quantity_extraction']}",
              f"  candidate selection   {s['candidate_selection']}",
              f"  max_add_food respected {s['max_add_food_respected']}",
              f"  errors                {s['errors']}"]
    t = report["thresholds"]
    lines += ["", "Draft thresholds (await owner approval): "
              f"case_pass>={t['case_pass_rate']}, clarification>={t['clarification_accuracy']}, "
              f"quantity>={t['quantity_extraction']}"]
    return "\n".join(lines)


def load_report(path: str | Path) -> dict:
    """Load a previously saved runner report without invoking a parser."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Batch Russian interpretation evaluation (hypothesis #1).")
    ap.add_argument("--parser", choices=["nebius", "stub"], default="nebius")
    ap.add_argument("--case", dest="only", default=None, help="Run one case id, e.g. INTAKE-003")
    ap.add_argument("--prompt", default=None,
                    help="Path to a candidate system prompt for A/B (nebius only); default uses production")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    ap.add_argument("--render-json", metavar="PATH",
                    help="Render a previously saved JSON report; makes no parser calls")
    args = ap.parse_args(argv)

    if args.render_json:
        try:
            report = load_report(args.render_json)
        except (OSError, json.JSONDecodeError) as exc:
            ap.error(f"cannot read report {args.render_json!r}: {exc}")
        print(format_report(report))
        return 0

    report = run(args.parser, args.only, args.prompt)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
