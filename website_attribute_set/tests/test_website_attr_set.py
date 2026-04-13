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

        # Create required attribute records directly for test compatibility
        cls.group_1 = cls.env["attribute.group"].create(
            {
                "name": "Technical Group",
                "model_id": cls.product_model.id,
                "sequence": 1,
            }
        )

        cls.attr_set_1 = cls.env["attribute.set"].create(
            {
                "name": "Computer Attribute Set",
                "model_id": cls.product_model.id,
            }
        )

        cls.attr_1 = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Processor",
                "name": "x_processor",
                "attribute_type": "select",
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(4, cls.attr_set_1.id)],
                "model_id": cls.product_model.id,
            }
        )

        cls.attr_2 = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Technical Description",
                "name": "x_technical_description",
                "attribute_type": "text",
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(4, cls.attr_set_1.id)],
                "model_id": cls.product_model.id,
            }
        )
        cls.attr_3 = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Hard Disk",
                "name": "x_hard_disk",
                "attribute_type": "select",
                "attribute_group_id": cls.group_1.id,  # Using group created directly
                "attribute_set_ids": [
                    (
                        4,
                        cls.attr_set_1.id,  # Using the set we created directly
                        0,
                    )
                ],
                "model_id": cls.product_model.id,  # Using the model we already have
                "relation_model_id": cls.product_model.id,
            }
        )
        # Create an attribute with domain capabilities for domain validation test
        cls.attr_select = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Test Domain Attribute",
                "name": "x_test_domain_attr",
                "attribute_type": "select",
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(4, cls.attr_set_1.id)],
                "model_id": cls.product_model.id,
                "relation_model_id": cls.product_model.id,
            }
        )

        cls.attr_binary = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Document",
                "name": "x_document",
                "attribute_type": "binary",
                "attribute_group_id": cls.group_1.id,
                "attribute_set_ids": [(4, cls.attr_set_1.id)],
                "model_id": cls.product_model.id,
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
        # Test invalid domain raises ValidationError
        # ir_model._check_domain intercepts ValueError from safe_eval and re-raises
        # it as ValidationError before our own _validate_domain constraint runs.
        with self.assertRaises(ValidationError):
            self.attr_select.domain = "foo"

        # Test that a valid domain can be set without error
        self.attr_select.domain = ["|", ["name", "!=", "foo"], ["name", "!=", "foo"]]

        # Test that a structurally invalid domain raises our custom ValidationError
        # We create a new record and call the constraint method directly
        # to ensure the validation logic is tested independent of framework behavior.
        invalid_domain_list = [["name", "!=", "foo"], "|", ["name", "!=", "foo"]]
        # The domain field is a Char, so the list is stored as its string representation
        invalid_domain_str = str(invalid_domain_list)
        record_with_invalid_domain = self.env["attribute.attribute"].new(
            {"domain": invalid_domain_str}
        )
        with self.assertRaises(ValidationError):
            record_with_invalid_domain._validate_domain()

        # Test that other valid domains can be set
        self.attr_select.domain = [("name", "!=", "foo")]
        self.attr_select.domain = []

    def test_get_extra_attributes(self):
        # Assert the method returns no attributes if they are not visible in e-com app
        extra_attrs = self.product_1.get_extra_attributes()
        self.assertFalse(extra_attrs)
        # Assert the method returns only the attributes that are visible in e-com app
        # Create a test option for the processor attribute
        test_option = self.env["attribute.option"].create(
            {
                "name": "Intel i7",
                "attribute_id": self.attr_1.id,
            }
        )
        self.product_1.x_processor = test_option
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
        # attributes are not searchable in e-com
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(list(domain), [(0, "=", 1)])
        # attributes are searchable in e-com but
        # if they are select or multi-select then
        # they need relation_model_id value
        self.attr_1.write({"e_com_searchable": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(list(domain), [(0, "=", 1)])
        # attributes are searchable in e-com
        self.attr_2.write({"e_com_searchable": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(
            list(domain), [("x_technical_description", "ilike", "Fast processor")]
        )
        # select, multi-select attributes are searchable in e-com as
        # they have relation_model_id value
        self.attr_3.write({"e_com_searchable": True})
        domain = search_extra(self.env, "Fast processor")
        self.assertEqual(
            list(domain),
            [
                "|",
                ("x_hard_disk.name", "ilike", "Fast processor"),
                ("x_technical_description", "ilike", "Fast processor"),
            ],
        )

    def test_e_com_searchable_vs_visibility(self):
        """Test that e_com_searchable controls search, not e_com_visibility."""
        # Set attribute visible but NOT searchable
        self.attr_2.write({"e_com_visibility": True, "e_com_searchable": False})
        domain = search_extra(self.env, "Fast processor")
        # Should NOT include this attribute in search
        self.assertEqual(list(domain), [(0, "=", 1)])

        # Now make it searchable
        self.attr_2.write({"e_com_searchable": True})
        domain = search_extra(self.env, "Fast processor")
        # Should include this attribute in search
        self.assertEqual(
            list(domain), [("x_technical_description", "ilike", "Fast processor")]
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
        # custom attributes appear in e-com search if we set searchable
        self.attr_2.write({"e_com_searchable": True})
        self.attr_3.write({"e_com_searchable": True})
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
        # ordered dict exists if products are visible in e-com
        self.product_1.write({"x_technical_description": "Fast processor"})
        self.attr_2.write({"e_com_visibility": True})
        groups = product_1._prepare_additional_attributes_for_display()
        self.assertTrue(self.group_1 in groups)
        self.assertTrue(self.attr_2 in groups[self.group_1])
        self.assertTrue(product_1 in groups[self.group_1][self.attr_2])

    def test_get_extra_attribute_values_binary(self):
        # Without a value, returns None
        self.assertIsNone(self.product_1.get_extra_attribute_values(self.attr_binary))
        # For binary attributes, the filename field is read instead of the binary itself
        self.product_1.write({"x_document_filename": "datasheet.pdf"})
        self.assertEqual(
            self.product_1.get_extra_attribute_values(self.attr_binary),
            "datasheet.pdf",
        )

    def test__prepare_simple_additional_attributes_for_display(self):
        # Empty when no attribute is e-com visible
        groups = self.product_1._prepare_simple_additional_attributes_for_display()
        self.assertFalse(groups)
        # Attribute with a value and e_com_visibility appears in groups
        self.product_1.write({"x_technical_description": "Fast processor"})
        self.attr_2.write({"e_com_visibility": True})
        groups = self.product_1._prepare_simple_additional_attributes_for_display()
        self.assertIn(self.group_1, groups)
        self.assertIn(self.attr_2, groups[self.group_1])
        self.assertEqual(groups[self.group_1][self.attr_2], "Fast processor")
        # Attribute with no value is excluded from groups
        self.attr_1.write({"e_com_visibility": True})
        groups = self.product_1._prepare_simple_additional_attributes_for_display()
        self.assertNotIn(self.attr_1, groups[self.group_1])
