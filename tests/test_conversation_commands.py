import unittest

from nutrition_app.conversation import is_standalone_latest_delete


class StandaloneDeleteCommandTests(unittest.TestCase):
    def test_supported_latest_delete_phrasings(self):
        for text in (
            "Удали последнее",
            "удалить последнюю запись",
            "УБЕРИ последнюю еду!",
            "Сотри последнюю порцию…",
            "стереть последний прием",
            "Удали",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_standalone_latest_delete(text))

    def test_named_delete_is_not_treated_as_latest_delete(self):
        for text in ("Удали творог", "Удали запись номер 2", "Удали вчерашний суп", "Удали эту еду"):
            with self.subTest(text=text):
                self.assertFalse(is_standalone_latest_delete(text))
