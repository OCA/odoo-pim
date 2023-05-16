from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestSelection(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "=", "a")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "=", "b")]),
            self.universe_book,
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "!=", "a")]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "!=", "b")]),
            self.jungle_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "in", ["a"])]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_selection", "in", ["a", "b"])]
            ),
            self.jungle_book | self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search(
                [
                    (
                        "x_attr_selection",
                        "in",
                        ["j"],
                    )
                ]
            ),
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_selection", "not in", ["a"])]
            ),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search(
                [("x_attr_selection", "not in", ["a", "b"])]
            )
        )
        self.assertEqual(
            self.env["product.template"].search(
                [
                    (
                        "x_attr_selection",
                        "not in",
                        ["j"],
                    )
                ]
            ),
            self.jungle_book | self.universe_book,
        )

    def test_equal_like(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "=like", "a")]),
            self.jungle_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_selection", "=like", "A")]),
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "=like", "b")]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_selection", "=like", "B")]),
        )

    def test_less(self):
        self.assertFalse(
            self.env["product.template"].search([("x_attr_selection", "<", "a")]),
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "<", "b")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "<", "c")]),
            self.jungle_book | self.universe_book,
        )

    def test_less_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "<=", "a")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", "<=", "b")]),
            self.jungle_book | self.universe_book,
        )

    def test_greater(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", ">", "a")]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_selection", ">", "b")]),
        )

    def test_greater_equal(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", ">=", "a")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"].search([("x_attr_selection", ">=", "b")]),
            self.universe_book,
        )
