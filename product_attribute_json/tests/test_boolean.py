from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestBoolean(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_bool", "=", True)]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_bool", "=", False)]),
            self.universe_book,
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_bool", "!=", True)]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_bool", "!=", False)]),
            self.jungle_book,
        )
