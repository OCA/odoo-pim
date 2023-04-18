from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestText(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "=", "Mowgli est un enfant sauvage")]
            ),
            self.jungle_book,
        )
        self.assertFalse(
            self.env["product.template"].search(
                [("x_attr_text", "=", "Mowgli est un enfant accro au téléphone")]
            ),
        )
        self.assertFalse(
            self.env["product.template"].search([("x_attr_text", "=", "Mowgli")])
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "!=", "Mowgli est un enfant sauvage")]
            ),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "!=", "Mowgli est un enfant accro au téléphone")]
            ),
            self.jungle_book | self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"].search([("x_attr_text", "!=", "Mowgli")]),
            self.jungle_book | self.universe_book,
        )

    def test_less_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "<=", "Mowgli est un enfant sauvage")]
            ),
            self.jungle_book | self.universe_book,
        )

    def test_less_than(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_text", "<", "z")]),
            self.jungle_book | self.universe_book,
        )

    def test_greater_than(self):
        self.assertFalse(
            self.env["product.template"].search(
                [("x_attr_text", ">", "Mowgli est un enfant sauvage")]
            )
        )

    def test_greater_than_equal(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", ">=", "Mowgli est un enfant sauvage")]
            ),
            self.jungle_book,
        )

    def test_equal_like(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "=like", "Mowgli est un enfant sauvage")]
            ),
            self.jungle_book,
        )

    def test_equal_ilike(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "=ilike", "Mowgli est Un enfant sauVAge")]
            ),
            self.jungle_book,
        )

    def test_like(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_text", "like", "enfant")]),
            self.jungle_book,
        )

    def test_not_like(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "not like", "Mowgli est un enfant sauvage")]
            ),
            self.universe_book,
        )

    def test_ilike(self):
        self.assertEqual(
            self.env["product.template"].search([("x_attr_text", "ilike", "saUvage")]),
            self.jungle_book,
        )

    def test_not_ilike(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "not ilike", "Mowgli est un enfant sauvage")]
            ),
            self.universe_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "in", ["Mowgli est un enfant sauvage"])]
            ),
            self.jungle_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"].search(
                [("x_attr_text", "not in", ["Mowgli est un enfant sauvage"])]
            ),
            self.universe_book,
        )
