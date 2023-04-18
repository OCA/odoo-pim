from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestInteger(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "=", 2)]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "=", 1)]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_integer", "=", 0)])
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "!=", 2)]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "!=", 1)]),
            self.jungle_book,
        )

    def test_less_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "<=", 2)]),
            self.jungle_book | self.universe_book,
        )

    def test_less_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "<", 2)]),
            self.universe_book,
        )

    def test_greater_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", ">", 1)]),
            self.jungle_book,
        )

    def test_greater_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", ">=", 2)]),
            self.jungle_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "in", [2])]),
            self.jungle_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_integer", "not in", [2])]),
            self.universe_book,
        )
