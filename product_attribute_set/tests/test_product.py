# Copyright 2025 Kencove (http://kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import lxml.etree as ET

from odoo.tests.common import Form, TransactionCase


class TestProductAttributeSet(TransactionCase):
    def setUp(self):
        self.ProductTemplate = self.env["product.template"]
        self.view_id = self.env.ref("product.product_template_only_form_view").id
        self.computer = self.env.ref("product_attribute_set.computer_attribute_set")
        self.x_technical_description = self.env.ref(
            "product_attribute_set.computer_tech_description_attribute"
        )
        super().setUp()

    def test_onchange_attribute_set_id(self):
        """Test that onchange on attribute_set_id is triggered and view fields are updated"""

        product = None

        with self.assertRaises(AssertionError):
            # AssertionError: can't write on invisible field x_technical_description
            with Form(self.ProductTemplate) as f:
                f.name = "Test Product"
                f.x_technical_description = "high quality product"
                f.save()
        with Form(self.ProductTemplate) as f:
            f.name = "Test Product"
            f.attribute_set_id = self.computer
            f.x_technical_description = "high quality product"
            product = f.save()
        # Asserting the field is only writeable when it is visible
        self.assertEqual(
            product.x_technical_description,
            "high quality product",
        )

        views = product.get_views([(self.view_id, "form")], {})
        arch = views["views"]["form"]["arch"]
        xml_arch = ET.fromstring(arch)
        field_node = xml_arch.xpath("//field[@name='x_technical_description']")
        self.assertTrue(field_node)
        field_node = field_node[0]
        attrs = field_node.get("attrs")
        mocked_attrs = (
            "{{'invisible': [('attribute_set_id', 'not in', [{id}])]}}".format(
                id=self.computer.id
            )
        )
        # This domain as it is rendered with attributes,
        # it will make them visible only if the attribute_set_id is set
        self.assertEqual(attrs, mocked_attrs)
