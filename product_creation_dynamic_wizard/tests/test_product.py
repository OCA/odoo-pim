from lxml import etree
from parameterized import parameterized

from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestProduct(SavepointCase):
    @parameterized.expand([("product.template"), ("product.product",)])
    def test_action_open_product_creation_dynamic_wizard(self, model):
        action = self.env[model].action_open_product_creation_dynamic_wizard()
        wizard = self.env["product.creation.dynamic.wizard"].browse(action["res_id"])
        self.assertTrue(wizard.exists())
        self.assertEqual(wizard.current_step, 0)

    @parameterized.expand([("product.template"), ("product.product",)])
    def test_load_views_button_create_disabled(self, model):
        self.env["ir.config_parameter"].set_param(
            "product_creation_dynamic_wizard.disable_create_product_button", "True"
        )
        result = self.env[model].load_views(
            [
                (False, "list"),
                (False, "form"),
                (False, "kanban"),
                (False, "pivot"),
            ]
        )
        for view in result["fields_views"].values():
            doc = etree.XML(view["arch"])
            self.assertTrue(doc.attrib.get("create", False))

    @parameterized.expand([("product.template"), ("product.product",)])
    def test_load_views_button_create_not_disabled(self, model):
        result = self.env[model].load_views(
            [
                (False, "list"),
                (False, "form"),
                (False, "kanban"),
                (False, "pivot"),
            ]
        )
        for view in result["fields_views"].values():
            doc = etree.XML(view["arch"])
            self.assertFalse(doc.attrib.get("create", False))

    def test_update_cache(self):
        # in some fields (likes seller_ids) the wizard will call
        # onchange that call _update_cache on product.template with
        # wizard fields current_*, testing that _update_cache
        # using those fields do not raises
        template = self.env["product.template"].new()
        template.with_context(product_creation_wizard=True)._update_cache(
            {"current_wizard_field": "test", "name": "valid product template field"}
        )
        self.assertEqual(
            self.env.cache.get(template, self.env["product.template"]._fields["name"]),
            "valid product template field",
        )

    def test_update_cache_without_context_pass(self):
        # hydrating the update cache must be done only on wizard context
        template = self.env["product.template"].new()
        template._update_cache({"name": "valid product template field"})
        self.assertEqual(
            self.env.cache.get(template, self.env["product.template"]._fields["name"]),
            "valid product template field",
        )

    def test_update_cache_without_context_failed(self):
        # hydrating the update cache must be done only on wizard context
        with self.assertRaisesRegex(
            ValueError,
            r"Invalid field 'current_wizard_field' on model 'product.template'",
        ):
            self.env["product.template"].new()._update_cache(
                {"current_wizard_field": "test", "name": "other field"}
            )
