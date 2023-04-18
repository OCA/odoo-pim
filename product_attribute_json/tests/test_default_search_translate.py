from odoo.addons.product_attribute_json.tests.test_common import TestCommon


class TestDefaultSearchTranslate(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.life_book = (
            cls.env["product.template"]
            .with_context(lang="en_US")
            .create(
                {
                    "name": "Life book",
                    "default_code": "LIFE",
                    "x_attr_char": "Life",
                    "x_attr_bool": True,
                    "x_attr_char_translate": "Life",
                    "x_attr_float": 2.3,
                    "x_attr_integer": 2,
                    "x_attr_monetary": 10.0,
                    "x_attr_selection": "a",
                    "x_attr_text": "The life is beautiful",
                    "x_attr_text_translated": "The life is beautiful",
                    "attribute_set_id": cls.attribute_set.id,
                }
            )
        )

    def test_translate_search_english(self):

        french_product = self.env["product.template"].with_context(lang="fr_FR")

        self.assertEqual(
            french_product.search([("x_attr_char_translate", "=", "Life")]),
            self.life_book,
        )
