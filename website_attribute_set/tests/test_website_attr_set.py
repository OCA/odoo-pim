# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.attribute_set_test.tests.test_build_view import BuildViewCase
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
        with self.assertRaises(ValidationError):
            self.attr_select.domain = "foo"
        self.attr_select.domain = ["|", ["name", "!=", "foo"], ["name", "!=", "foo"]]
        with self.assertRaises(ValidationError):
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

    def test_search_extra_integer_float_attributes(self):
        """Test search_extra with integer and float attribute types."""
        # Create an integer attribute
        attr_int = self.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Quantity",
                "name": "x_quantity",
                "attribute_type": "integer",
                "attribute_group_id": self.group_1.id,
                "attribute_set_ids": [(4, self.attr_set_1.id, 0)],
                "model_id": self.product_model.id,
                "e_com_visibility": True,
            }
        )
        # Create a float attribute
        attr_float = self.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Custom Weight",
                "name": "x_custom_weight",
                "attribute_type": "float",
                "attribute_group_id": self.group_1.id,
                "attribute_set_ids": [(4, self.attr_set_1.id, 0)],
                "model_id": self.product_model.id,
                "e_com_visibility": True,
            }
        )
        # Test with numeric search term
        domain = search_extra(self.env, "123")
        self.assertTrue(any("x_quantity" in str(d) for d in domain))
        # Test with float search term
        domain = search_extra(self.env, "12.5")
        self.assertTrue(any("x_custom_weight" in str(d) for d in domain))
        # Test with non-numeric search term (should trigger ValueError handling)
        domain = search_extra(self.env, "not a number")
        # Should not include integer/float fields when search term is not numeric
        self.assertFalse(any("x_quantity" in str(d) for d in domain))
        # Cleanup
        attr_int.unlink()
        attr_float.unlink()

    def test_search_extra_similarity_matching(self):
        """Test search_extra with similarity matching for boolean/date types."""
        # Create a boolean attribute (not char/text/int/float/select)
        attr_bool = self.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Is Active",
                "name": "x_is_active",
                "attribute_type": "boolean",
                "attribute_group_id": self.group_1.id,
                "attribute_set_ids": [(4, self.attr_set_1.id, 0)],
                "model_id": self.product_model.id,
                "e_com_visibility": True,
            }
        )
        # Test with search term very similar to field_description (>80% match)
        domain = search_extra(self.env, "Is Active")
        self.assertTrue(any("x_is_active" in str(d) for d in domain))
        # Test with dissimilar search term (<80% match)
        domain = search_extra(self.env, "completely different")
        self.assertFalse(any("x_is_active" in str(d) for d in domain))
        # Cleanup
        attr_bool.unlink()

    def test_website_search_get_details_with_additional_attribs(self):
        """Test Website._search_get_details with additional attribute filtering."""
        self.attr_2.write({"e_com_visibility": True})
        self.product_1.write({"x_technical_description": "Fast processor"})
        website = self.env["website"].browse(1)
        # Test with simple attribute value
        options = {
            "additional_attrib_values": [[self.attr_2.id, "Fast processor"]],
            "displayDescription": False,
            "displayDetail": False,
            "displayExtraDetail": False,
            "displayExtraLink": False,
            "displayImage": False,
            "allowFuzzy": True,
        }
        details = website._search_get_details("all", "name asc", options)
        self.assertTrue(details)
        # Test with name-model-id format (for select/multiselect)
        self.attr_1.write({"e_com_visibility": True})
        option_1 = self.env.ref(
            "product_attribute_set.computer_processor_attribute_option_1"
        )
        self.product_1.x_processor = option_1
        options_select = {
            "additional_attrib_values": [
                [
                    self.attr_1.id,
                    f"name-{option_1._name}-id-{option_1.id}",
                ]
            ],
            "displayDescription": False,
            "displayDetail": False,
            "displayExtraDetail": False,
            "displayExtraLink": False,
            "displayImage": False,
            "allowFuzzy": True,
        }
        details = website._search_get_details("all", "name asc", options_select)
        self.assertTrue(details)

    def test_get_extra_attributes_no_attribute_set(self):
        """Test get_extra_attributes when product has no attribute_set_id."""
        product_no_set = self.env["product.template"].create(
            {
                "name": "Product Without Attribute Set",
                "type": "consu",
            }
        )
        # Should return empty recordset when no attribute_set_id
        extra_attrs = product_no_set.get_extra_attributes()
        self.assertFalse(extra_attrs.ids)
        product_no_set.unlink()

    def test_get_extra_attribute_values_no_attribute(self):
        """Test get_extra_attribute_values with no attribute parameter."""
        result = self.product_1.get_extra_attribute_values()
        self.assertIsNone(result)
