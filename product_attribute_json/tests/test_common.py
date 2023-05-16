from contextlib import contextmanager

from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):
    jungle_book = None

    @classmethod
    @contextmanager
    def _simulate_pool_loaded(cls):
        """
        Simulate the pool loaded state.
        This is needed for Odoo to create monetary fields
        """
        save_loaded = cls.env["ir.model.fields"].pool.loaded
        cls.env["ir.model.fields"].pool.loaded = True
        yield
        cls.env["ir.model.fields"].pool.loaded = save_loaded

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("fr_FR")
        cls.env["res.lang"]._activate_lang("en_US")
        cls.product_model = cls.env["ir.model"].search(
            [("model", "=", "product.template")]
        )
        cls.attribute_group = cls.env["attribute.group"].create(
            {"name": "Test attribute group", "model_id": cls.product_model.id}
        )

        attribute_set = cls.env["attribute.set"].create(
            {
                "name": "Test attribute set",
                "model_id": cls.product_model.id,
            }
        )

        attribute_model = cls.env["attribute.attribute"]

        default_attribute_value = {
            "nature": "json_postgresql",
            "model_id": cls.product_model.id,
            "size": 0,
            "serialized": False,
            "field_id": False,
            "attribute_group_id": cls.attribute_group.id,
            "sequence": 0,
            "widget": False,
            "domain": "[]",
            "option_ids": [],
            "required": False,
            "store": False,
            "state": "manual",
            "attribute_set_ids": [(6, 0, [attribute_set.id])],
        }

        attribute_model.create(
            {
                "name": "x_attr_bool",
                "attribute_type": "boolean",
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_integer",
                "attribute_type": "integer",
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_float",
                "attribute_type": "float",
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_char",
                "attribute_type": "char",
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_text",
                "attribute_type": "text",
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_char_translate",
                "attribute_type": "char",
                "translate": True,
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_selection",
                "attribute_type": "selection",
                "selection": [("a", "A"), ("b", "B")],
                **default_attribute_value,
            }
        )

        attribute_model.create(
            {
                "name": "x_attr_text_translated",
                "attribute_type": "text",
                "translate": True,
                **default_attribute_value,
            }
        )

        with cls._simulate_pool_loaded():
            attribute_model.create(
                {
                    "name": "x_attr_monetary",
                    "attribute_type": "monetary",
                    **default_attribute_value,
                }
            )

        cls.jungle_book = (
            cls.env["product.template"]
            .with_context(lang="fr_FR")
            .create(
                {
                    "name": "Jungle Book",
                    "default_code": "jungle_book",
                    "x_attr_char": "Jungle",
                    "x_attr_bool": True,
                    "x_attr_char_translate": "Jungle",
                    "x_attr_float": 2.3,
                    "x_attr_integer": 2,
                    "x_attr_monetary": 10.0,
                    "x_attr_selection": "a",
                    "x_attr_text": "Mowgli est un enfant sauvage",
                    "x_attr_text_translated": "Mowgli est un enfant sauvage",
                    "attribute_set_id": attribute_set.id,
                }
            )
        )

        cls.universe_book = (
            cls.env["product.template"]
            .with_context(lang="fr_FR")
            .create(
                {
                    "name": "Universe Book",
                    "default_code": "universe_book",
                    "x_attr_char": "Universe Book",
                    "x_attr_bool": False,
                    "x_attr_char_translate": "Univers",
                    "x_attr_float": 2.6,
                    "x_attr_integer": 1,
                    "x_attr_monetary": 42.42,
                    "x_attr_selection": "b",
                    "x_attr_text": "L'univers est immense",
                    "x_attr_text_translated": "L'univers est immense",
                    "attribute_set_id": attribute_set.id,
                }
            )
        )

        cls.universe_book.with_context(lang="en_US").x_attr_char_translate = "Universe"

        cls.jungle_book.with_context(
            lang="en_US"
        ).x_attr_text_translated = "Mowgli is a wild child"
        cls.addClassCleanup(cls.cleanUp, cls)

    def cleanUp(self):
        # Remove all attributes created so the inverse compute and search
        # methods are removed from the model before the next initialization
        self.env["attribute.attribute"].search(
            [("nature", "=", "json_postgresql")]
        ).unlink()
