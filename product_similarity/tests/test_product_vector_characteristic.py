# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.errors import CheckViolation

from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

from .common import TestProductSimilarityCommon


class TestProductVectorCharacteristic(TestProductSimilarityCommon):
    def _create_m2m(self, value_id, **vals):
        return self.Characteristic.create(
            dict(field_id=self.many_to_many_field.id, value_id=value_id, **vals)
        )

    def test_ensure_vector_index_starts_at_0(self):
        characteristic = self.Characteristic.create(
            {"field_id": self.boolean_field.id, "weight": 1}
        )
        self.assertEqual(characteristic.vector_index, 0)

    def test_vector_index_fits_hole(self):
        value_ids = list(self.many_to_many_field_values)
        char_1 = self._create_m2m(value_ids[0])
        char_2 = self._create_m2m(value_ids[1])
        char_3 = self._create_m2m(value_ids[2])
        self.assertEqual(char_1.vector_index, 0)
        self.assertEqual(char_2.vector_index, 1)
        self.assertEqual(char_3.vector_index, 2)

        char_2.unlink()
        char_4 = self._create_m2m(value_ids[1])
        self.assertEqual(char_4.vector_index, 1)

    def test_vector_index_multi_create(self):
        value_ids = list(self.many_to_many_field_values)[:3]
        characteristics = self.Characteristic.create(
            [
                {"field_id": self.many_to_many_field.id, "value_id": value_id}
                for value_id in value_ids
            ]
        )
        self.assertEqual(characteristics.mapped("vector_index"), [0, 1, 2])

    def test_prevent_creation_for_invalid_value_id(self):
        value_ids = list(self.many_to_many_field_values)
        with self.assertRaises(ValidationError):
            self._create_m2m(max(value_ids) + 1)

    def test_prevent_duplicate_vector_index(self):
        value_ids = list(self.many_to_many_field_values)
        # A given vector_index is ignored, a free one is assigned
        char_1 = self._create_m2m(value_ids[0], vector_index=0)
        char_2 = self._create_m2m(value_ids[1], vector_index=0)
        self.assertEqual(char_1.vector_index, 0)
        self.assertEqual(char_2.vector_index, 1)

    @mute_logger("odoo.sql_db")
    def test_weight_must_be_positive(self):
        with self.assertRaises(CheckViolation):
            self.Characteristic.create({"field_id": self.boolean_field.id, "weight": 0})

    def test_boolean_characteristic(self):
        characteristic = self.Characteristic.create({"field_id": self.boolean_field.id})
        self.assertEqual(characteristic.name, "sale_ok")
        self.assertFalse(characteristic.value_id_visible)
        self.assertFalse(characteristic.value_name)
        self.assertFalse(characteristic.possible_values_string)
        self.assertEqual(characteristic.model_id.model, "product.product")

    def test_relational_characteristic(self):
        tag = self.env["product.tag"].search([("name", "=", "green")], limit=1)
        characteristic = self._create_m2m(tag.id)
        self.assertTrue(characteristic.value_id_visible)
        self.assertEqual(characteristic.value_name, "green")
        self.assertEqual(characteristic.name, "product_tag_ids = 'green'")
        self.assertEqual(characteristic.model_id.model, "product.tag")
        self.assertIn("green", characteristic.possible_values_string)

    def test_selection_characteristic(self):
        selection = self.selection_field.selection_ids[0]
        characteristic = self.Characteristic.create(
            {"field_id": self.selection_field.id, "value_id": selection.id}
        )
        self.assertEqual(characteristic.value_name, selection.display_name)
        self.assertEqual(characteristic.model_id.model, "product.product")

    def test_unsupported_field_type(self):
        char_field = self._get_field("default_code")
        self.assertFalse(self.Characteristic.get_related_model(char_field))
