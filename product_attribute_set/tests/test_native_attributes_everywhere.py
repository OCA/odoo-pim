# Copyright 2026 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import TransactionCase

from ..models.product import SHOW_NATIVE_EVERYWHERE_PARAM


class TestNativeAttributesEverywhere(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.models = {
            "product.template": "x_test_template_custom",
            "product.product": "x_test_variant_custom",
        }
        for model, custom_name in cls.models.items():
            cls._create_attributes(model, custom_name)

    @classmethod
    def _create_attributes(cls, model, custom_name):
        ir_model = cls.env["ir.model"]._get(model)
        attribute_set = cls.env["attribute.set"].create(
            {"name": f"Set {model}", "model_id": ir_model.id}
        )
        group = cls.env["attribute.group"].create(
            {"name": f"Group {model}", "model_id": ir_model.id}
        )
        common_vals = {
            "attribute_group_id": group.id,
            "attribute_set_ids": [(6, 0, attribute_set.ids)],
        }
        cls.env["attribute.attribute"].create(
            [
                dict(
                    common_vals,
                    nature="custom",
                    name=custom_name,
                    attribute_type="char",
                    model_id=ir_model.id,
                ),
                dict(
                    common_vals,
                    nature="native",
                    attribute_type="text",
                    field_id=cls.env["ir.model.fields"]
                    ._get(model, "description_sale")
                    .id,
                ),
            ]
        )

    def _get_form(self, model):
        return etree.fromstring(self.env[model].get_view(view_type="form")["arch"])

    def _get_attribute_tab_fields(self, form):
        page = form.xpath("//page[@name='product_attributes']")
        return set(page[0].xpath(".//field/@name"))

    def test_setting_disabled(self):
        for model, custom_name in self.models.items():
            with self.subTest(model=model):
                form = self._get_form(model)
                tab_fields = self._get_attribute_tab_fields(form)
                self.assertIn(custom_name, tab_fields)
                self.assertNotIn("description_sale", tab_fields)
                self.assertTrue(form.xpath("//field[@name='description_sale']"))

    def test_setting_enabled(self):
        self.env["ir.config_parameter"].set_param(SHOW_NATIVE_EVERYWHERE_PARAM, True)
        for model, custom_name in self.models.items():
            with self.subTest(model=model):
                form = self._get_form(model)
                tab_fields = self._get_attribute_tab_fields(form)
                self.assertIn(custom_name, tab_fields)
                self.assertIn("description_sale", tab_fields)
                self.assertEqual(
                    len(form.xpath("//field[@name='description_sale']")), 1
                )
