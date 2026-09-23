"""Evaluation-only Nebius parser without model-authored evidence.

This module deliberately does not change the production parser contract. It
removes the free-text ``evidence`` property from the provider-facing schema,
then derives the audit excerpt from the original source message after the
provider response passes the diagnostic schema. The derived value is only a
fixture for measuring candidate and quantity extraction; it is not an
authorization path and must not be used by the application worker.
"""

from __future__ import annotations

from copy import deepcopy
import json

from jsonschema import Draft202012Validator

from nutrition_app.nebius import (
    HOST,
    ENDPOINT,
    MAX_BYTES,
    REQUEST_POLICY,
    TIMEOUT_SECONDS,
    NebiusParser,
)
from nutrition_app.service import digest
from nutrition_contracts.parser import ParserOutput


def diagnostic_schema() -> dict:
    """Return a copy of ParserOutput's schema with model evidence removed."""
    schema = deepcopy(ParserOutput.model_json_schema())
    for definition in schema.get("$defs", {}).values():
        properties = definition.get("properties")
        required = definition.get("required")
        if isinstance(properties, dict) and "evidence" in properties:
            properties.pop("evidence")
        if isinstance(required, list) and "evidence" in required:
            required.remove("evidence")
    Draft202012Validator.check_schema(schema)
    return schema


class DiagnosticNebiusParser(NebiusParser):
    """Nebius transport using the no-model-evidence diagnostic contract."""

    def __init__(self, config, *, request=None, prompt=None):
        super().__init__(config, request=request, prompt=prompt)
        self._schema = diagnostic_schema()
        self._response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "nutrition_parser_diagnostic_no_evidence",
                "schema": self._schema,
                "strict": True,
            },
        }
        self._diagnostic_validator = Draft202012Validator(self._schema)
        self.version = "nebius-diagnostic-no-evidence:" + digest({
            "adapter": "nebius-chat-v3-diagnostic-no-evidence",
            "model": config.model,
            "prompt": self._prompt,
            "schema": self._schema,
            "policy": REQUEST_POLICY,
            "host": HOST,
            "endpoint": ENDPOINT,
            "timeout": TIMEOUT_SECONDS,
            "max_bytes": MAX_BYTES,
            "response_format": self._response_format,
        })

    def _parse_content(self, content: str, request):
        raw = json.loads(content)
        self._diagnostic_validator.validate(raw)
        if not isinstance(raw, dict) or not isinstance(raw.get("actions"), list):
            raise ValueError("diagnostic output is not an action object")
        # This is intentionally backend-derived test data. The provider did
        # not author or validate these excerpts.
        for action in raw["actions"]:
            action["evidence"] = request.source_text
        return ParserOutput.model_validate(raw)
