"""PostgreSQL checks for trusted local product provisioning."""

from uuid import uuid4
import unittest

import sqlalchemy as sa
from sqlalchemy.engine import make_url

from nutrition_app.catalog import create_product
from nutrition_app.db import database_url, engine_for, migrate
from nutrition_app import schema as db
from nutrition_app.errors import ApplicationError


class CatalogProvisioningTests(unittest.TestCase):
    def setUp(self):
        url = database_url()
        if make_url(url).host not in {"127.0.0.1", "localhost", "::1"}:
            self.fail("Integration tests require a local disposable development database")
        self.admin = engine_for(url)
        self.schema = "ntest_catalog_" + uuid4().hex
        with self.admin.begin() as connection:
            connection.execute(sa.schema.CreateSchema(self.schema))
        self.engine = engine_for(url, schema=self.schema)
        migrate(self.engine)
        self.actor = uuid4()
        with self.engine.begin() as connection:
            connection.execute(db.users.insert().values(id=self.actor, time_zone="Europe/Berlin"))
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.engine.dispose()
        with self.admin.begin() as connection:
            connection.execute(sa.schema.DropSchema(self.schema, cascade=True, if_exists=True))
        self.admin.dispose()

    def test_creates_owner_scoped_versioned_product(self):
        result = create_product(self.engine, self.actor, name="Яблоко",
                                 nutrition={"kcal": "52", "protein_g": "0.3", "fat_g": "0.2", "carbs_g": "14"})
        with self.engine.connect() as connection:
            product = connection.execute(sa.select(db.products).where(db.products.c.user_id == self.actor)).mappings().one()
            version = connection.execute(sa.select(db.product_versions).where(
                db.product_versions.c.user_id == self.actor)).mappings().one()
            source = connection.execute(sa.select(db.data_sources).where(
                db.data_sources.c.user_id == self.actor)).mappings().one()
        self.assertEqual(result["product_id"], str(product["id"]))
        self.assertEqual(product["current_version_id"], version["id"])
        self.assertEqual(version["name"], "Яблоко")
        self.assertEqual(str(version["kcal"]), "52.000000")
        self.assertEqual(source["kind"], "operator_catalog")

    def test_requires_nutrition_and_valid_dairy_percentage(self):
        with self.assertRaisesRegex(ApplicationError, "nutrition value"):
            create_product(self.engine, self.actor, name="Без данных", nutrition={
                "kcal": None, "protein_g": None, "fat_g": None, "carbs_g": None})
        with self.assertRaisesRegex(ApplicationError, "food kind dairy"):
            create_product(self.engine, self.actor, name="Не молочное", nutrition={"kcal": "1"},
                           declared_fat_percent="5")


if __name__ == "__main__":
    unittest.main()
