from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestChar(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "=", "Jungle")]),
            self.jungle_book,
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "!=", "Jungle")]),
            self.universe_book,
        )

    def test_less_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "<=", "Jungle")]),
            self.jungle_book,
        )

    def test_less_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "<", "A")]),
            self.env["product.template"],
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "<", "Z")]),
            self.jungle_book | self.universe_book,
        )

    def test_greater_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", ">", "Jungle")]),
            self.universe_book,
        )

    def test_greater_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", ">=", "Jungle")]),
            self.jungle_book | self.universe_book,
        )

    def test_equal_like(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "=like", "Jungle")]),
            self.jungle_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_char", "=like", "jungle")]),
        )

    def test_equal_ilike(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "=ilike", "JUNGLE")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "=ilike", "jungle")]),
            self.jungle_book,
        )

    def test_like(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "like", "Jungle")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "like", "jungle")]),
            self.env["product.template"],
        )

    def test_not_like(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_char", "not like", "Jungle")]
            ),
            self.universe_book,
        )

    def test_ilike(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "ilike", "JUNGLE")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "ilike", "jungle")]),
            self.jungle_book,
        )

    def test_not_ilike(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_char", "not ilike", "Jungle")]
            ),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_char", "not ilike", "jungle")]
            ),
            self.universe_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_char", "in", ["Jungle"])]),
            self.jungle_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_char", "not in", ["Jungle"])]
            ),
            self.universe_book,
        )
