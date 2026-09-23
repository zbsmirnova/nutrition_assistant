"""Nebius Token Factory boundary; no provider response authorizes a mutation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import http.client
import json
import math
import os
from pathlib import Path
import re
from uuid import UUID

from nutrition_contracts.parser import ParserOutput, validate_parser_context

from .errors import ApplicationError
from .interpretation import (MAX_CANDIDATES, ParserRejected, ParserRequest,
                             ParserUnavailable, parser_request, resolve)
from .service import digest


HOST = "api.tokenfactory.nebius.com"
ENDPOINT = "/v1/chat/completions"
TIMEOUT_SECONDS = 30
MAX_BYTES = 256 * 1024
MAX_RETRY_AFTER = 86400
REQUEST_POLICY = {"max_tokens": 4096, "temperature": 0, "n": 1, "stream": False}
PROMPT = Path(__file__).with_name("nebius_prompt.txt").read_text(encoding="utf-8")


class NebiusConfigurationError(ApplicationError):
    code = "nebius_configuration"


@dataclass(frozen=True)
class NebiusConfig:
    api_key: str = field(repr=False)
    model: str

    def __post_init__(self):
        if (not isinstance(self.api_key, str) or not re.fullmatch(r"[!-~]{1,4096}", self.api_key)
                or not isinstance(self.model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}", self.model)):
            raise NebiusConfigurationError("Set valid NEBIUS_API_KEY and NUTRITION_LLM_MODEL through local configuration")

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("NEBIUS_API_KEY", ""), os.environ.get("NUTRITION_LLM_MODEL", ""))


def retry_after_seconds(headers):
    value = headers.get("retry-after")
    if value is None:
        return None
    try:
        if not isinstance(value, str) or len(value) > 128:
            raise ValueError
        value = value.strip(" \t")  # HTTP optional whitespace is not part of the field value.
        if re.fullmatch(r"[0-9]+", value):
            seconds = int(value)
        else:
            instant = parsedate_to_datetime(value)
            if instant.tzinfo is None:
                raise ValueError
            seconds = max(0, math.ceil((instant - datetime.now(timezone.utc)).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return None
    if seconds > MAX_RETRY_AFTER:
        raise ParserRejected("Provider retry delay exceeds the supported one-day limit")
    return seconds


class NebiusParser:
    """One request per parse; retry policy belongs to the durable worker."""

    def __init__(self, config: NebiusConfig, *, request=None):
        self._config = config
        self._schema = ParserOutput.model_json_schema()
        self._response_format = {"type": "json_schema", "json_schema": {
            "name": "nutrition_parser_output", "schema": self._schema, "strict": True}}
        self._request = request or self._https
        self.version = "nebius:" + digest({"adapter": "nebius-chat-v3", "model": config.model,
            "prompt": PROMPT, "schema": self._schema, "policy": REQUEST_POLICY,
            "host": HOST, "endpoint": ENDPOINT, "timeout": TIMEOUT_SECONDS,
            "max_bytes": MAX_BYTES, "response_format": self._response_format})

    def _payload(self, request: ParserRequest):
        if len(request.candidates) > MAX_CANDIDATES:
            raise ParserRejected("Provider context exceeds the supported catalog limit")
        # Explicit projection even if a caller accidentally supplies private candidate keys.
        keys = ("ref", "name", "nutrition_basis", "weight_basis", "food_kind", "declared_fat_percent")
        context = {"source_text": request.source_text, "local_date": request.local_date,
                   "time_zone": request.time_zone,
                   "candidates": [{key: candidate[key] for key in keys} for candidate in request.candidates]}
        if request.entries:
            context["entries"] = [{key: candidate[key] for key in ("ref", "description", "effective_date", "meal", "state")}
                                   for candidate in request.entries]
        if request.pending_entries:
            context["pending_entries"] = [{key: candidate[key] for key in ("ref", "description", "effective_date", "meal", "state")}
                                           for candidate in request.pending_entries]
        if request.pending_questions:
            context["pending_candidates"] = [{key: candidate[key] for key in keys}
                                               for candidate in request.pending_candidates]
            context["pending_questions"] = request.pending_questions
        payload = {"model": self._config.model, **REQUEST_POLICY,
            "messages": [{"role": "system", "content": PROMPT + "\nJSON Schema:\n" + json.dumps(self._schema)},
                         {"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
            "response_format": self._response_format}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(body) > MAX_BYTES:
            raise ParserRejected("Provider request exceeds the supported size limit")
        return body

    def _https(self, body, timeout):
        connection = http.client.HTTPSConnection(HOST, timeout=timeout)
        try:
            connection.request("POST", ENDPOINT, body=body, headers={
                "Content-Type": "application/json", "Accept": "application/json",
                "Authorization": "Bearer " + self._config.api_key})
            response = connection.getresponse()
            # Error bodies can echo secrets/input; do not read or retain them.
            headers = {"retry-after": response.getheader("Retry-After")}
            raw = response.read(MAX_BYTES + 1) if response.status == 200 else b""
            return response.status, headers, raw
        finally:
            connection.close()

    def parse(self, request: ParserRequest) -> str:
        try:
            body = self._payload(request)
        except ParserRejected:
            raise
        except Exception:
            raise ParserRejected("Invalid provider context") from None
        try:
            status, headers, raw = self._request(body, TIMEOUT_SECONDS)
        except Exception:
            raise ParserUnavailable("Nebius request unavailable") from None
        if type(status) is not int or not isinstance(headers, dict):
            raise ParserRejected("Invalid provider response envelope")
        if status in {408, 429} or 500 <= status <= 599:
            delay = retry_after_seconds({str(k).lower(): v for k, v in headers.items()})
            if delay is None and status == 429:
                delay = 60
            raise ParserUnavailable("Nebius temporarily unavailable", retry_after=delay)
        if status != 200:
            raise ParserRejected(f"Nebius rejected the request (HTTP {status}); check credentials, model and schema support")
        try:
            if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
                raise ValueError
            response = json.loads(raw)
            if not isinstance(response, dict) or response.get("error") is not None:
                raise ValueError
            choices = response["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError
            choice = choices[0]
            if choice.get("finish_reason") != "stop" or type(choice.get("index")) is not int or choice["index"] != 0:
                raise ValueError
            message = choice["message"]
            if (message.get("role") != "assistant" or message.get("refusal") is not None
                    or message.get("tool_calls") or message.get("function_call") is not None):
                raise ValueError
            content = message["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError
            # Local schema/graph validation remains mandatory even with structured output.
            output = ParserOutput.model_validate_json(content)
            candidate_kinds = {c["ref"]: "product" for c in request.candidates}
            candidate_kinds.update({c["ref"]: "entry" for c in request.entries})
            candidate_kinds.update({c["ref"]: {"pending", "product"} for c in request.pending_candidates})
            candidate_kinds.update({c["ref"]: {"pending", "entry"} for c in request.pending_entries})
            validate_parser_context(output, candidate_kinds, request.pending_questions,
                                    source_text=request.source_text, has_reply=request.has_reply)
        except Exception:
            raise ParserRejected("Invalid, incomplete or refused Nebius interpretation") from None
        return output.model_dump_json()


def run_synthetic_smoke(parser: NebiusParser):
    """One fixed synthetic request; no database connection and no payload output."""
    from .conversation_demo import PRODUCT_NAME, TEXT
    context = {"source_text": TEXT, "local_date": "2026-09-22", "time_zone": "Europe/Berlin", "context_revision": 0,
        "has_reply": False, "forwarded": False, "candidates": [{"ref": "c1", "name": PRODUCT_NAME,
        "version_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc", "nutrition_basis": "per_100_g",
        "weight_basis": "as_sold", "food_kind": "dairy", "declared_fat_percent": "5"}]}
    output = ParserOutput.model_validate_json(parser.parse(parser_request(context)))
    result = resolve(UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                     UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), context, output)
    reason = result.reason if result.status != "ready" else None
    if result.status == "ready":
        food = result.command.command.food
        if Decimal(food.components[0].quantity.edible_g) != Decimal("100"):
            reason = "unexpected_quantity"
        elif food.effective_date.isoformat() != "2026-09-22":
            reason = "unexpected_date"
    if reason is not None:
        # Kinds are schema literals; status/reason are backend-defined codes.
        # Model-provided paths are free text, so expose only known field names.
        paths = {"food", "food.name", "food.candidate_ref", "food.candidate_kind", "quantity",
                 "quantity.amount", "quantity.unit", "weight_basis", "date_hint", "date_hint.text", "meal"}
        unresolved = sorted({item.path if item.path in paths else "other"
                             for action in output.actions for item in action.unresolved})
        kinds = sorted({action.kind for action in output.actions})
        raise ParserRejected("Synthetic smoke response did not match the expected food action "
            f"(schema_valid=true; actions={','.join(kinds)}; resolution={result.status}; reason={reason}; "
            f"unresolved_fields={','.join(unresolved) or 'none'})")
    return {"provider": "nebius", "synthetic": True, "schema_valid": True, "expected_action_matched": True,
            "parser_version": parser.version}
