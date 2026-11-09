# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestProductAttributeSetCompleteness(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        model_id = cls.env.ref("product.model_product_template").id
        group = cls.env["attribute.group"].create(
            {"name": "Machine", "model_id": model_id}
        )
        vals = {
            "nature": "custom",
            "model_id": model_id,
            "attribute_type": "char",
            "field_description": "Power",
            "name": "x_power",
            "attribute_group_id": group.id,
        }
        cls.attr_power = cls.env["attribute.attribute"].create(vals)
        vals.update({"name": "x_height", "field_description": "Height"})
        cls.attr_height = cls.env["attribute.attribute"].create(vals)
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "Machines",
                "model_id": model_id,
                "attribute_ids": [
                    Command.link(cls.attr_power.id),
                    Command.link(cls.attr_height.id),
                ],
                "attribute_set_completeness_ids": [
                    Command.create(
                        {
                            "field_id": cls.attr_power.field_id.id,
                            "completion_rate": 60.0,
                        }
                    ),
                    Command.create(
                        {
                            "field_id": cls.attr_height.field_id.id,
                            "completion_rate": 40.0,
                        }
                    ),
                ],
            }
        )
        cls.template = cls.env["product.template"].create(
            {"name": "Forklift", "attribute_set_id": cls.attr_set.id}
        )
        cls.variant = cls.template.product_variant_id

    def test_completion_template_and_variant(self):
        self.assertEqual(self.template.attribute_set_completion_rate, 0.0)
        self.assertEqual(self.variant.attribute_set_completion_rate, 0.0)
        self.template.x_power = "50 kW"
        self.assertEqual(self.template.attribute_set_completion_rate, 60.0)
        self.assertEqual(self.variant.attribute_set_completion_rate, 60.0)
        self.variant.x_height = "2 m"
        self.assertEqual(self.template.attribute_set_completion_rate, 100.0)
        self.assertEqual(self.template.attribute_set_completion_state, "complete")
        self.assertEqual(self.variant.attribute_set_completion_rate, 100.0)
        self.assertEqual(self.variant.attribute_set_completion_state, "complete")

    def test_search_filters(self):
        self.template.write({"x_power": "50 kW", "x_height": "2 m"})
        other = self.template.copy({"x_power": False, "x_height": False})
        no_set = self.env["product.template"].create({"name": "Pallet"})
        self.env.flush_all()
        templates = self.template | other | no_set
        self.assertEqual(
            templates.search(
                [
                    ("id", "in", templates.ids),
                    ("attribute_set_completion_state", "=", "complete"),
                ]
            ),
            self.template,
        )
        self.assertEqual(
            self.env["product.product"].search(
                [
                    ("product_tmpl_id", "in", templates.ids),
                    ("attribute_set_completion_state", "=", "not_complete"),
                ]
            ),
            other.product_variant_ids,
        )

    def test_views(self):
        form = etree.fromstring(
            self.env["product.template"].get_view(view_type="form")["arch"]
        )
        for fname in (
            "attribute_set_completion_state",
            "attribute_set_completion_rate",
            "attribute_set_not_completed_ids",
        ):
            self.assertTrue(form.xpath(f"//field[@name='{fname}']"), fname)
        search = etree.fromstring(
            self.env["product.template"].get_view(view_type="search")["arch"]
        )
        self.assertTrue(search.xpath("//filter[@name='filter_not_complete']"))
