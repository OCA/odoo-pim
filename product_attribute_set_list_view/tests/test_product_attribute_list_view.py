# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import TransactionCase


class TestProductAttributeListView(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_id = cls.env.ref("product.model_product_template").id
        cls.attribute_set = cls.env["attribute.set"].create(
            {"name": "Set X", "model_id": cls.model_id}
        )
        cls.group = cls.env["attribute.group"].create(
            {"name": "Tech", "model_id": cls.model_id}
        )
        cls.attr_char = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "attribute_type": "char",
                "field_description": "Material",
                "name": "x_listview_material",
                "attribute_group_id": cls.group.id,
                "model_id": cls.model_id,
                "attribute_set_ids": [(4, cls.attribute_set.id)],
            }
        )
        cls.attr_select = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "attribute_type": "select",
                "field_description": "Color",
                "name": "x_listview_color",
                "attribute_group_id": cls.group.id,
                "model_id": cls.model_id,
                "attribute_set_ids": [(4, cls.attribute_set.id)],
                "option_ids": [
                    (0, 0, {"name": "Red"}),
                    (0, 0, {"name": "Blue"}),
                ],
            }
        )
        cls.product1 = cls.env["product.template"].create(
            {"name": "P1", "attribute_set_id": cls.attribute_set.id}
        )
        cls.product2 = cls.env["product.template"].create(
            {"name": "P2", "attribute_set_id": cls.attribute_set.id}
        )

    def test_list_view_contains_attribute_columns(self):
        result = self.env["product.template"].get_view(view_type="list")
        arch = etree.fromstring(result["arch"])
        list_node = arch if arch.tag == "list" else arch.find(".//list")
        self.assertIsNotNone(list_node)
        field_names = [f.get("name") for f in list_node.xpath("./field")]
        self.assertIn("x_listview_material", field_names)
        self.assertIn("x_listview_color", field_names)

    def test_attribute_columns_are_optional_hidden(self):
        result = self.env["product.template"].get_view(view_type="list")
        arch = etree.fromstring(result["arch"])
        material_field = arch.find(".//field[@name='x_listview_material']")
        self.assertEqual(material_field.get("optional"), "hide")

    def test_multi_edit_is_enabled(self):
        result = self.env["product.template"].get_view(view_type="list")
        arch = etree.fromstring(result["arch"])
        list_node = arch if arch.tag == "list" else arch.find(".//list")
        self.assertEqual(list_node.get("multi_edit"), "1")

    def test_value_can_be_written(self):
        # Multi-edit on the UI ultimately calls write on the recordset.
        (self.product1 + self.product2).write({"x_listview_material": "Steel"})
        self.assertEqual(self.product1.x_listview_material, "Steel")
        self.assertEqual(self.product2.x_listview_material, "Steel")
