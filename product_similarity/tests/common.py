# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

class TestProductSimilarityCommon(TransactionCase):
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