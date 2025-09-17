# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestProductVectorCharacteristic(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.boolean_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "product.product"),
                ("name", "=", "sale_ok"),
            ]
        )

        cls.selection_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "product.product"),
                ("name", "=", "activity_exception_decoration"),
            ]
        )
        cls.selection_field_values = cls.env[
            "product.vector.characteristic"
        ].get_possible_values(cls.selection_field)

        cls.many_to_many_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "product.product"),
                ("name", "=", "product_tag_ids"),
            ]
        )
        cls.env[cls.many_to_many_field.relation].create(
            [{"name": n} for n in ["red", "green", "blue"]]
        )
        cls.many_to_many_field_values = cls.env[
            "product.vector.characteristic"
        ].get_possible_values(cls.many_to_many_field)

        cls.many_to_one_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "product.product"),
                ("name", "=", "cost_currency_id"),
            ]
        )
        cls.many_to_one_field_values = cls.env[
            "product.vector.characteristic"
        ].get_possible_values(cls.many_to_one_field)

    def test_ensure_vector_index_starts_at_0(self):
        vector_characteristic = self.env["product.vector.characteristic"].create(
            {"field_id": self.boolean_field.id, "weight": 1}
        )
        self.assertEqual(vector_characteristic.vector_index, 0)

    def test_vector_index_fits_hole(self):
        possible_value_ids = list(self.many_to_many_field_values)
        vector_characteristic_1 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[0],
                "weight": 1,
            }
        )
        vector_characteristic_2 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[1],
                "weight": 1,
            }
        )
        vector_characteristic_3 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[2],
                "weight": 1,
            }
        )

        self.assertEqual(vector_characteristic_1.vector_index, 0)
        self.assertEqual(vector_characteristic_2.vector_index, 1)
        self.assertEqual(vector_characteristic_3.vector_index, 2)

        vector_characteristic_2.unlink()
        vector_characteristic_4 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[1],
                "weight": 1,
            }
        )
        self.assertEqual(vector_characteristic_4.vector_index, 1)
    
    def test_prevent_creation_for_invalid_value_id(self):
        possible_value_ids = list(self.many_to_many_field_values)

        with self.assertRaises(UserError):
            vector_characteristic_1 = self.env["product.vector.characteristic"].create(
                {
                    "field_id": self.many_to_many_field.id,
                    "value_id": sum(possible_value_ids),
                    "weight": 1,
                }
            )

    def test_prevent_duplicate_vector_index(self):
        possible_value_ids = list(self.many_to_many_field_values)
        vector_characteristic_1 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[0],
                "weight": 1,
                "vector_index": 0 # <- should not be taken into account
            }
        )
        vector_characteristic_2 = self.env["product.vector.characteristic"].create(
            {
                "field_id": self.many_to_many_field.id,
                "value_id": possible_value_ids[1],
                "weight": 1,
                "vector_index": 0 # <- should not be taken into account
            }
        )
        self.assertEqual(vector_characteristic_1.vector_index, 0)
        self.assertEqual(vector_characteristic_2.vector_index, 1)
