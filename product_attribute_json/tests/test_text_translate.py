from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestTextTranslate(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "=", "Mowgli est un enfant sauvage")]),
            self.jungle_book,
        )

        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_text_translated", "=", "Sri Lanka Survival Guide")])
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "!=", "Mowgli est un enfant sauvage")]),
            self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "!=", "Guide de survie au Sri Lanka")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_text_translated", "!=", "Sri Lanka Survival Guide")]),
            self.jungle_book | self.universe_book,
        )

    def test_like(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "like", "Mowgli")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "like", "est")]),
            self.jungle_book | self.universe_book,
        )

    def test_not_like(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "not like", "Lanka")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "not like", "Mowgli")]),
            self.universe_book,
        )

    def test_ilike(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "ilike", "mowgli")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "ilike", "est")]),
            self.jungle_book | self.universe_book,
        )

    def test_not_ilike(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "not ilike", "Lanka")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "not ilike", "mowgli")]),
            self.universe_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search(
                [("x_attr_text_translated", "in", ["Mowgli est un enfant sauvage"])]
            ),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search(
                [
                    (
                        "x_attr_text_translated",
                        "in",
                        ["Mowgli est un enfant sauvage", "L'univers est immense"],
                    )
                ]
            ),
            self.jungle_book | self.universe_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search(
                [("x_attr_text_translated", "not in", ["Mowgli est un enfant sauvage"])]
            ),
            self.universe_book,
        )

        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search(
                [
                    (
                        "x_attr_text_translated",
                        "not in",
                        ["Mowgli est un enfant sauvage", "L'univers est immense"],
                    )
                ]
            )
        )

    def test_greater(self):
        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", ">", "Mowgli est un enfant sauvage")])
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", ">", "L'univers est immense")]),
            self.jungle_book,
        )

    def test_greater_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", ">=", "Mowgli est un enfant sauvage")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", ">=", "L'univers est immense")]),
            self.jungle_book | self.universe_book,
        )

    def test_less(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "<", "Mowgli est un enfant sauvage")]),
            self.universe_book,
        )

        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "<", "L'univers est immense")])
        )

    def test_less_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "<=", "Mowgli est un enfant sauvage")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_text_translated", "<=", "L'univers est immense")]),
            self.universe_book,
        )
