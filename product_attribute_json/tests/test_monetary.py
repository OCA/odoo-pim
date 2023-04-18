from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestMonetary(TestCommon):
    def test_in(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "in", [10.00])]),
            self.jungle_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_monetary", "not in", [10.00])]
            ),
            self.universe_book,
        )

    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "=", 10.00)]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "=", 42.42)]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_monetary", "=", 0.00)])
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "!=", 10.00)]),
            self.universe_book,
        )

    def test_less_than(self):
        self.assertFalse(
            self.env["product.template"].search([("x_attr_monetary", "<", 10.00)]),
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "<", 42.42)]),
            self.jungle_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_monetary", "<", 0.00)])
        )

    def test_less_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", "<=", 10.00)]),
            self.jungle_book,
        )

    def test_greater_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", ">", 10.00)]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_monetary", ">", 42.42)]),
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", ">", 0.00)]),
            self.jungle_book | self.universe_book,
        )

    def test_greater_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", ">=", 10.01)]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_monetary", ">=", 10.00)]),
            self.jungle_book | self.universe_book,
        )
