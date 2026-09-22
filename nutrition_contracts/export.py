"""Run `python -m nutrition_contracts.export` to regenerate portable schemas."""

import json
from pathlib import Path

from .commands import CommandEnvelope
from .parser import ParserOutput
from .results import OutcomeEnvelope


SCHEMA_MODELS = {
    "parser-output": ParserOutput,
    "command": CommandEnvelope,
    "outcome": OutcomeEnvelope,
}
SCHEMA_DIRECTORY = Path(__file__).resolve().parents[1] / "contracts" / "v1"


def schema_for(name: str) -> dict:
    schema = SCHEMA_MODELS[name].model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:nutrition-assistant:contracts:1.0:{name}"
    return schema


def main() -> None:
    SCHEMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name in SCHEMA_MODELS:
        path = SCHEMA_DIRECTORY / f"{name}.schema.json"
        path.write_text(json.dumps(schema_for(name), indent=2, ensure_ascii=False) + "\n")
        print(f"Generated {path.name}")


if __name__ == "__main__":
    main()
