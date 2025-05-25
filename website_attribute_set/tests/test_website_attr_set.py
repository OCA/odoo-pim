# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.attribute_set.tests.test_build_view import BuildViewCase
from odoo.addons.website_attribute_set.models.mixins import search_extra


class TestAttributeSetSearchable(BuildViewCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env.ref("product.model_product_template")
        cls.attr_set_1 = cls.env.ref("product_attribute_set.computer_attribute_set")
        cls.group_1 = cls.env.ref(
            "product_attribute_set.computer_technical_attribute_group"
        )
        cls.attr_1 = cls.env.ref("product_attribute_set.computer_processor_attribute")
        cls.attr_2 = cls.env.ref(
            "product_attribute_set.computer_tech_description_attribute"
        )
        cls.attr_3 = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Hard Disk",
                "name": "x_hard_disk",
                "attribute_type": "select",
                "attribute_group_id": cls.env.ref(
                    "product_attribute_set.computer_technical_attribute_group"
                ).id,
                "attribute_set_ids": [
                    (
                        4,
                        cls.env.ref("product_attribute_set.computer_attribute_set").id,
                        0,
                    )
                ],
                "model_id": cls.env.ref("product.model_product_template").id,
                "relation_model_id": cls.product_model.id,
            }
        )
        cls.product_1 = cls.env["product.template"].create(
            {
                "name": "Test Smart Product",
                "type": "consu",
                "attribute_set_id": cls.attr_set_1.id,
            }
        )

    def test__validate_domain(self):
        with self.assertRaisesRegex(ValueError, r"name 'foo' is not defined"):
            self.attr_select.domain = "foo"
        self.attr_select.domain = ["|", ["name", "!=", "foo"], ["name", "!=", "foo"]]
        with self.assertRaisesRegex(ValidationError, r"Invalid domain: "):
            # Displace the "|" to the second position which is not correct
            self.attr_select.domain = [
                ["name", "!=", "foo"],
                "|",
                ["name", "!=", "foo"],
            ]
        self.attr_select.domain = [("name", "!=", "foo")]
        self.attr_select.domain = []

    def test_get_extra_attributes(self):
        # Assert the method returns no attributes if they are not visible in e-com app
        extra_attrs = self.product_1.get_extra_attributes()
        self.assertFalse(extra_attrs)
        # Assert the method returns only the attributes that are visible in e-com app
        self.product_1.x_processor = self.env.ref(
            "product_attribute_set.computer_processor_attribute_option_1"
        )
        self.product_1.write({"x_technical_description": "Fast processor"})
        self.attr_1.write({"e_com_visibility": True})
        extra_attrs = self.product_1.get_extra_attributes()
        self.assertTrue(
            len(extra_attrs) == 1 and extra_attrs.mapped("name") == ["x_processor"]
        )
        self.attr_2.write({"e_com_visibility": True})
        extra_attrs = self.product_1.get_extra_attributes()
        self.assertTrue(
            len(extra_attrs) == 2
            and extra_attrs.mapped("name") == ["x_processor", "x_technical_description"]
        )

    def test_search_extra(self):
        # attributes are not visible in e-com
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(domain, [(0, "=", 1)])
        # attributes are visible in e-com but
        # if they are select or multi-select then
        # they need relation_model_id value
        self.attr_1.write({"e_com_visibility": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(domain, [(0, "=", 1)])
        # attributes are visible in e-com
        self.attr_2.write({"e_com_visibility": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(
            domain, [("x_technical_description", "ilike", "Fast processor")]
        )
        # select, multi-select attributes are visible in e-com as
        # they have relation_model_id value
        self.attr_3.write({"e_com_visibility": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(
            domain,
            [
                "|",
                ("x_hard_disk.name", "ilike", "Fast processor"),
                ("x_technical_description", "ilike", "Fast processor"),
            ],
        )

    def test__search_fetch(self):
        self.product_1.write({"x_technical_description": "Fast processor"})
        custom_domain = [
            "&",
            "&",
            ("sale_ok", "=", True),
            ("website_id", "in", (False, 1)),
            "|",
            "|",
            "|",
            ("name", "ilike", "Fast"),
            ("default_code", "ilike", "Fast"),
            ("product_variant_ids.default_code", "ilike", "Fast"),
            "|",
            ("x_hard_disk.name", "ilike", "Fast"),
            ("x_technical_description", "ilike", "Fast"),
        ]
        result = self.env["product.template"].search(custom_domain)
        # custom attributes don't appear in e-com search of we don't set visibility
        results = (
            self.env["website"]
            .browse(1)
            ._search_with_fuzzy(
                "all",
                "Fast",
                limit=5,
                order="name asc, website_id desc, id",
                options={
                    "displayDescription": False,
                    "displayDetail": False,
                    "displayExtraDetail": False,
                    "displayExtraLink": False,
                    "displayImage": False,
                    "allowFuzzy": True,
                },
            )
        )
        for i in results[1]:
            self.assertEqual(i["count"], 0)
        # custom attributes appear in e-com search of we set visibility
        self.attr_2.write({"e_com_visibility": True})
        self.attr_3.write({"e_com_visibility": True})
        results = (
            self.env["website"]
            .browse(1)
            ._search_with_fuzzy(
                "all",
                "Fast",
                limit=5,
                order="name asc, website_id desc, id",
                options={
                    "displayDescription": False,
                    "displayDetail": False,
                    "displayExtraDetail": False,
                    "displayExtraLink": False,
                    "displayImage": False,
                    "allowFuzzy": True,
                },
            )
        )
        for i in results[1]:
            if i["count"] > 0:
                self.assertEqual(i["count"], 1)
                self.assertEqual(i["results"].mapped("name"), ["Test Smart Product"])
                self.assertEqual(i["results"], result)

    def test_get_extra_attribute_values(self):
        extra_attribute_values = self.product_1.get_extra_attribute_values(self.attr_2)
        self.assertEqual(extra_attribute_values, None)
        self.product_1.write({"x_technical_description": "Fast processor"})
        extra_attribute_values = self.product_1.get_extra_attribute_values(self.attr_2)
        self.assertEqual(extra_attribute_values, "Fast processor")

    def test__prepare_additional_attributes_for_display(self):
        # ordered dict is empty if products are not visible in e-com
        product_1 = self.env["product.product"].search(
            [("name", "=", "Test Smart Product")]
        )
        groups = product_1._prepare_additional_attributes_for_display()
        self.assertFalse(groups)
        # ordered dict is exists if products are visible in e-com
        self.product_1.write({"x_technical_description": "Fast processor"})
        self.attr_1.write({"e_com_visibility": True})
        groups = product_1._prepare_additional_attributes_for_display()
        self.assertTrue(self.group_1 in groups)
        self.assertTrue(self.attr_1 in groups[self.group_1])
        self.assertTrue(product_1 in groups[self.group_1][self.attr_1])
