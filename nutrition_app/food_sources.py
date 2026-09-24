"""External food-catalog adapters used only for cold-start lookup.

Adapters return untrusted candidates.  They never write food entries or decide
which candidate the user consumed; the conversation worker caches a candidate
and asks for confirmation before the product can enter a diary total.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import http.client
import json
import os
from typing import Callable, Protocol
from urllib.parse import urlencode

from .errors import ApplicationError


class FoodSourceUnavailable(ApplicationError):
    code = "food_source_unavailable"


class FoodSource(Protocol):
    name: str

    def search(self, query: str, *, limit: int = 5) -> list["ExternalFoodCandidate"]: ...


@dataclass(frozen=True)
class ExternalFoodCandidate:
    provider: str
    external_id: str
    name: str
    kcal: str | None
    protein_g: str | None
    fat_g: str | None
    carbs_g: str | None
    nutrition_basis: str = "per_100_g"
    weight_basis: str = "as_sold"
    food_kind: str = "general"
    declared_fat_percent: str | None = None
    source_name: str | None = None
    license: str | None = None

    def usable(self) -> bool:
        return any(value is not None for value in
                   (self.kcal, self.protein_g, self.fat_g, self.carbs_g))


def _decimal(value) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number < 0:
        return None
    rendered = format(number, "f").rstrip("0").rstrip(".")
    return rendered or "0"


def _bounded_limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("food-source result limit must be between 1 and 20")
    return limit


class _HttpsJson:
    def __init__(self, *, timeout: int = 5, user_agent: str):
        if type(timeout) is not int or not 1 <= timeout <= 15:
            raise ValueError("food-source timeout must be between 1 and 15 seconds")
        self.timeout = timeout
        self.user_agent = user_agent

    def get(self, host: str, path: str) -> dict:
        connection = http.client.HTTPSConnection(host, timeout=self.timeout)
        try:
            connection.request("GET", path, headers={"Accept": "application/json",
                                                       "User-Agent": self.user_agent})
            response = connection.getresponse()
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024 or response.status != 200:
                raise FoodSourceUnavailable("Food source request unavailable")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise FoodSourceUnavailable("Food source returned an invalid response")
            return payload
        except FoodSourceUnavailable:
            raise
        except Exception:
            raise FoodSourceUnavailable("Food source request unavailable") from None
        finally:
            connection.close()


class OpenFoodFactsSource:
    name = "openfoodfacts"

    def __init__(self, *, request: Callable[[str, dict], dict] | None = None,
                 timeout: int = 5, user_agent: str = "NutritionAssistant/1.0 (contact unavailable)"):
        self._request = request
        self._http = _HttpsJson(timeout=timeout, user_agent=user_agent)

    @staticmethod
    def _weight_basis(product: dict) -> str:
        text = " ".join(str(product.get(key) or "") for key in
                         ("product_name", "generic_name", "categories" )).casefold()
        if any(token in text for token in ("raw", "сырой", "сырая", "сырое")):
            return "raw"
        if any(token in text for token in ("cooked", "boiled", "fried", "варен", "жарен", "готов")):
            return "cooked"
        return "as_sold"

    def search(self, query: str, *, limit: int = 5) -> list[ExternalFoodCandidate]:
        limit = _bounded_limit(limit)
        if not isinstance(query, str) or not query.strip():
            return []
        params = {"search_terms": query.strip(), "search_simple": "1", "action": "process",
                  "json": "1", "page_size": str(limit), "fields":
                  "code,product_name,product_name_ru,product_name_en,generic_name,nutriments"}
        payload = (self._request("/cgi/search.pl", params) if self._request is not None else
                   self._http.get("world.openfoodfacts.org", "/cgi/search.pl?" + urlencode(params)))
        products = payload.get("products")
        if not isinstance(products, list):
            raise FoodSourceUnavailable("Open Food Facts returned an invalid response")
        results = []
        for product in products:
            if not isinstance(product, dict):
                continue
            external_id = str(product.get("code") or "").strip()
            name = next((str(product.get(key)).strip() for key in
                         ("product_name_ru", "product_name", "product_name_en", "generic_name")
                         if product.get(key)), "")
            nutriments = product.get("nutriments")
            if not external_id or not name or not isinstance(nutriments, dict):
                continue
            values = {}
            for field, keys in {
                "kcal": ("energy-kcal_100g", "energy-kcal_value"),
                "protein_g": ("proteins_100g",),
                "fat_g": ("fat_100g",),
                "carbs_g": ("carbohydrates_100g",),
            }.items():
                values[field] = next((_decimal(nutriments.get(key)) for key in keys
                                      if _decimal(nutriments.get(key)) is not None), None)
            candidate = ExternalFoodCandidate(
                provider=self.name, external_id=external_id, name=name,
                source_name=name, license="ODbL/Database Contents License",
                weight_basis=self._weight_basis(product), **values)
            if candidate.usable():
                results.append(candidate)
        return results


class USDAFoodDataCentralSource:
    name = "usda_fdc"

    def __init__(self, api_key: str, *, request: Callable[[str, dict], dict] | None = None,
                 timeout: int = 5, user_agent: str = "NutritionAssistant/1.0"):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("USDA FoodData Central API key is required")
        self.api_key = api_key.strip()
        self._request = request
        self._http = _HttpsJson(timeout=timeout, user_agent=user_agent)

    @staticmethod
    def _weight_basis(description: str) -> str:
        text = description.casefold()
        if any(token in text for token in ("raw", "uncooked")):
            return "raw"
        if any(token in text for token in ("cooked", "boiled", "fried", "baked")):
            return "cooked"
        return "as_sold"

    @staticmethod
    def _nutrients(food: dict) -> dict[str, str | None]:
        values = {}
        for nutrient in food.get("foodNutrients", ()):
            if not isinstance(nutrient, dict):
                continue
            nutrient_id = nutrient.get("nutrientId")
            field = {1008: "kcal", 1003: "protein_g", 1004: "fat_g", 1005: "carbs_g"}.get(nutrient_id)
            if field is not None:
                values[field] = _decimal(nutrient.get("value"))
        return {field: values.get(field) for field in ("kcal", "protein_g", "fat_g", "carbs_g")}

    def search(self, query: str, *, limit: int = 5) -> list[ExternalFoodCandidate]:
        limit = _bounded_limit(limit)
        if not isinstance(query, str) or not query.strip():
            return []
        params = {"api_key": self.api_key, "query": query.strip(), "pageSize": str(limit),
                  "dataType": "Foundation,SR Legacy,Branded"}
        payload = (self._request("/fdc/v1/foods/search", params) if self._request is not None else
                   self._http.get("api.nal.usda.gov", "/fdc/v1/foods/search?" + urlencode(params)))
        foods = payload.get("foods")
        if not isinstance(foods, list):
            raise FoodSourceUnavailable("USDA FoodData Central returned an invalid response")
        results = []
        for food in foods:
            if not isinstance(food, dict):
                continue
            external_id = str(food.get("fdcId") or "").strip()
            name = str(food.get("description") or "").strip()
            if not external_id or not name:
                continue
            values = self._nutrients(food)
            candidate = ExternalFoodCandidate(provider=self.name, external_id=external_id,
                name=name, source_name=name, license="CC0 1.0", weight_basis=self._weight_basis(name), **values)
            if candidate.usable():
                results.append(candidate)
        return results


class CompositeFoodLookup:
    def __init__(self, sources: tuple[FoodSource, ...]):
        self.sources = sources

    def search(self, query: str, *, limit: int = 5) -> list[ExternalFoodCandidate]:
        results = []
        seen = set()
        failures = 0
        for source in self.sources:
            try:
                candidates = source.search(query, limit=limit)
            except FoodSourceUnavailable:
                failures += 1
                continue
            for candidate in candidates:
                key = (candidate.provider, candidate.external_id)
                if key not in seen:
                    seen.add(key)
                    results.append(candidate)
                if len(results) >= limit:
                    return results
        if not results and failures == len(self.sources) and self.sources:
            raise FoodSourceUnavailable("Food sources unavailable")
        return results


def lookup_from_environment() -> CompositeFoodLookup | None:
    """Build configured lookup providers; absent keys disable that provider."""
    sources: list[FoodSource] = []
    user_agent = os.environ.get("NUTRITION_FOOD_USER_AGENT", "NutritionAssistant/1.0 (local MVP)")
    sources.append(OpenFoodFactsSource(user_agent=user_agent))
    api_key = os.environ.get("USDA_FDC_API_KEY", "")
    if api_key:
        sources.append(USDAFoodDataCentralSource(api_key, user_agent=user_agent))
    return CompositeFoodLookup(tuple(sources)) if sources else None
