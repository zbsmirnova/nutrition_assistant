import unittest

from nutrition_app.food_sources import (CompositeFoodLookup, ExternalFoodCandidate,
                                        FoodSourceUnavailable, OpenFoodFactsSource,
                                        USDAFoodDataCentralSource)


class FoodSourceAdapterTests(unittest.TestCase):
    def test_open_food_facts_maps_russian_name_and_nutrients(self):
        def request(path, params):
            self.assertEqual(path, "/cgi/search.pl")
            self.assertEqual(params["search_terms"], "яблоко")
            return {"products": [{"code": "123", "product_name_ru": "Яблоко",
                "nutriments": {"energy-kcal_100g": 52, "proteins_100g": 0.3,
                                "fat_100g": 0.2, "carbohydrates_100g": 14}}]}

        result = OpenFoodFactsSource(request=request).search("яблоко")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Яблоко")
        self.assertEqual(result[0].kcal, "52")
        self.assertEqual(result[0].protein_g, "0.3")
        self.assertEqual(result[0].weight_basis, "as_sold")

    def test_open_food_facts_discards_product_without_usable_nutrition(self):
        result = OpenFoodFactsSource(request=lambda path, params: {
            "products": [{"code": "bad", "product_name": "Без данных", "nutriments": {}}]
        }).search("неизвестный продукт")
        self.assertEqual(result, [])

    def test_usda_maps_nutrient_ids_and_raw_basis(self):
        def request(path, params):
            self.assertEqual(path, "/fdc/v1/foods/search")
            self.assertEqual(params["api_key"], "test-key")
            self.assertNotIn("dataType", params)
            return {"foods": [{"fdcId": 42, "description": "Apple, raw, with skin",
                "foodNutrients": [{"nutrientId": 1008, "value": 52},
                                   {"nutrientId": 1003, "value": 0.3},
                                   {"nutrientId": 1004, "value": 0.2},
                                   {"nutrientId": 1005, "value": 14}]}]}

        result = USDAFoodDataCentralSource("test-key", request=request).search("apple")
        self.assertEqual(result[0].external_id, "42")
        self.assertEqual(result[0].carbs_g, "14")
        self.assertEqual(result[0].weight_basis, "raw")

    def test_composite_continues_after_unavailable_source_and_deduplicates(self):
        class Down:
            name = "down"
            def search(self, query, *, limit=5):
                raise FoodSourceUnavailable("offline")

        candidate = ExternalFoodCandidate("ok", "1", "яблоко", "52", "0.3", "0.2", "14")
        class Up:
            name = "up"
            def search(self, query, *, limit=5):
                return [candidate, candidate]

        result = CompositeFoodLookup((Down(), Up())).search("яблоко")
        self.assertEqual([(item.provider, item.external_id) for item in result], [("ok", "1")])
