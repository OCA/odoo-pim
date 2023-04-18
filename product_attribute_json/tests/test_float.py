from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestFloat(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_float", "=", 2.3)]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_float", "=", 2.6)]),
            self.universe_book,
        )

    def test_not_equal(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "!=", 2.3)]),
            self.universe_book,
            delta=0.01,
        )
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "!=", 2.6)]),
            self.jungle_book,
            delta=0.01,
        )

    def test_less_than_equal(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "<=", 2.3)]),
            self.jungle_book,
            delta=0.01,
        )

        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "<=", 2.6)]),
            self.jungle_book | self.universe_book,
            delta=0.01,
        )

    def test_less_than(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "<", 2.6)]),
            self.jungle_book,
            delta=0.01,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_float", "<", 2.3)])
        )

    def test_greater_than(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", ">", 2.3)]),
            self.universe_book,
            delta=0.01,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_float", ">", 2.6)])
        )

    def test_greater_than_equal(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", ">=", 2.2)]),
            self.jungle_book | self.universe_book,
            delta=0.01,
        )

    def test_in(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "in", [2.3])]),
            self.jungle_book,
            delta=0.01,
        )

    def test_not_in(self):
        self.assertAlmostEqual(
            self.env["product.template"].search([("x_attr_float", "not in", [2.3])]),
            self.universe_book,
            delta=0.01,
        )
