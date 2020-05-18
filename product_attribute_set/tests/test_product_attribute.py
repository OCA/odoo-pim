# Copyright 2018 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestProductAttribute(TransactionCase):
    def setUp(self):
        super(TestProductAttribute, self).setUp()
        self.product = self.env.ref("product.product_product_3")

    def test_write_attribute_values_text(self):
        self.product.write({"x_technical_description": "abcd"})
        self.assertEqual(self.product.x_technical_description, "abcd")

    def test_write_attribute_values_select(self):
        option = self.env.ref(
            "product_attribute_set.computer_processor_attribute_option_1"
        )
        self.product.write({"x_processor": option.id})
        self.assertEqual(self.product.x_processor, option)
