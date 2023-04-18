from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestCharTranslate(TestCommon):
    def test_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "=", "Jungle")]),
            self.jungle_book,
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "=", "Universe")]),
            self.universe_book,
        )

    def test_not_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "!=", "Jungle")]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "!=", "Universe")]),
            self.jungle_book,
        )

    def test_less(self):
        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "<", "Jungle")]),
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "<", "Universe")]),
            self.jungle_book,
        )

    def test_less_than_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "<=", "Jungle")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "<=", "Univers")]),
            self.jungle_book | self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "<=", "Universe")]),
            self.universe_book | self.jungle_book,
        )

    def test_greater(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", ">", "Jungle")]),
            self.universe_book,
        )
        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", ">", "Universe")])
        )

    def test_greater_than_equal(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", ">=", "Jungle")]),
            self.jungle_book | self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", ">=", "Universe")]),
            self.universe_book,
        )

    def test_in(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "in", ["Universe"])]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "in", ["Jungle", "Univers"])]),
            self.jungle_book | self.universe_book,
        )

    def test_not_in(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "not in", ["Universe"])]),
            self.jungle_book,
        )
        self.assertFalse(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "not in", ["Jungle", "Univers"])])
        )

    def test_like(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "like", "Universe")]),
            self.universe_book,
        )
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "like", "Jungle")]),
            self.jungle_book,
        )

    def test_not_like(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "not like", "Universe")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "not like", "Jungle")]),
            self.universe_book | self.jungle_book,
        )

    def test_ilike(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "ilike", "universe")]),
            self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "ilike", "jungle")]),
            self.jungle_book,
        )

    def test_not_ilike(self):
        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "not ilike", "universe")]),
            self.jungle_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="fr_FR")
            .search([("x_attr_char_translate", "not ilike", "jungle")]),
            self.universe_book,
        )

        self.assertEqual(
            self.env["product.template"]
            .with_context(lang="en_US")
            .search([("x_attr_char_translate", "not ilike", "Jungle")]),
            self.universe_book | self.jungle_book,
        )
