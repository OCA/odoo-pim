# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestProductSimilarityCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Characteristic = cls.env["product.vector.characteristic"]
        cls.Wizard = cls.env["product.field.vectorization.wizard"]
        cls.boolean_field = cls._get_field("sale_ok")
        cls.selection_field = cls._get_field("activity_exception_decoration")
        cls.many_to_many_field = cls._get_field("product_tag_ids")
        cls.many_to_one_field = cls._get_field("cost_currency_id")
        cls.env["product.tag"].create([{"name": n} for n in ["red", "green", "blue"]])
        cls.selection_field_values = cls.Characteristic.get_possible_values(
            cls.selection_field
        )
        cls.many_to_many_field_values = cls.Characteristic.get_possible_values(
            cls.many_to_many_field
        )
        cls.many_to_one_field_values = cls.Characteristic.get_possible_values(
            cls.many_to_one_field
        )

    @classmethod
    def _get_field(cls, name):
        return cls.env["ir.model.fields"]._get("product.product", name)
