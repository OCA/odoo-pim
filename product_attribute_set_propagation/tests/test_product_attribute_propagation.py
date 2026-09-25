# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestProductAttributePropagation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.cr.commit = mock.Mock()

        cls.tmpl_model_id = cls.env.ref("product.model_product_template").id
        cls.variant_model_id = cls.env.ref("product.model_product_product").id

        # Attribute group for product.template
        cls.tmpl_group = cls.env["attribute.group"].create(
            {
                "name": "Template Group",
                "model_id": cls.tmpl_model_id,
            }
        )
        # Attribute set for product.template
        cls.tmpl_attr_set = cls.env["attribute.set"].create(
            {
                "name": "Test Template Set",
                "model_id": cls.tmpl_model_id,
            }
        )
        # Char attribute
        cls.attr_char = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_char",
                "field_description": "Test Char",
                "attribute_type": "char",
                "attribute_group_id": cls.tmpl_group.id,
                "attribute_set_ids": [(6, 0, [cls.tmpl_attr_set.id])],
                "model_id": cls.tmpl_model_id,
            }
        )
        # Boolean attribute
        cls.attr_bool = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_bool",
                "field_description": "Test Boolean",
                "attribute_type": "boolean",
                "attribute_group_id": cls.tmpl_group.id,
                "attribute_set_ids": [(6, 0, [cls.tmpl_attr_set.id])],
                "model_id": cls.tmpl_model_id,
            }
        )
        # Select attribute
        cls.attr_select = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_select",
                "field_description": "Test Select",
                "attribute_type": "select",
                "attribute_group_id": cls.tmpl_group.id,
                "attribute_set_ids": [(6, 0, [cls.tmpl_attr_set.id])],
                "model_id": cls.tmpl_model_id,
            }
        )
        cls.select_option_1 = cls.env["attribute.option"].create(
            {"name": "Option A", "attribute_id": cls.attr_select.id}
        )
        cls.select_option_2 = cls.env["attribute.option"].create(
            {"name": "Option B", "attribute_id": cls.attr_select.id}
        )
        # Multiselect attribute
        cls.attr_multi = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_multi",
                "field_description": "Test Multi",
                "attribute_type": "multiselect",
                "attribute_group_id": cls.tmpl_group.id,
                "attribute_set_ids": [(6, 0, [cls.tmpl_attr_set.id])],
                "model_id": cls.tmpl_model_id,
                "option_ids": [
                    (0, 0, {"name": "Multi A"}),
                    (0, 0, {"name": "Multi B"}),
                    (0, 0, {"name": "Multi C"}),
                ],
            }
        )

        # Attribute group and set for product.product
        cls.variant_group = cls.env["attribute.group"].create(
            {
                "name": "Variant Group",
                "model_id": cls.variant_model_id,
            }
        )
        cls.variant_attr_set = cls.env["attribute.set"].create(
            {
                "name": "Test Variant Set",
                "model_id": cls.variant_model_id,
            }
        )
        cls.attr_variant_char = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_v_char",
                "field_description": "Variant Char",
                "attribute_type": "char",
                "attribute_group_id": cls.variant_group.id,
                "attribute_set_ids": [(6, 0, [cls.variant_attr_set.id])],
                "model_id": cls.variant_model_id,
            }
        )

        # Mixed attribute set: has attributes for both models
        cls.mixed_attr_set = cls.env["attribute.set"].create(
            {
                "name": "Test Mixed Set",
                "model_id": cls.tmpl_model_id,
            }
        )
        cls.attr_mixed_tmpl = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_mixed_t",
                "field_description": "Mixed Template Attr",
                "attribute_type": "char",
                "attribute_group_id": cls.tmpl_group.id,
                "attribute_set_ids": [(6, 0, [cls.mixed_attr_set.id])],
                "model_id": cls.tmpl_model_id,
            }
        )
        cls.attr_mixed_variant = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "name": "x_test_prop_mixed_v",
                "field_description": "Mixed Variant Attr",
                "attribute_type": "char",
                "attribute_group_id": cls.variant_group.id,
                "attribute_set_ids": [(6, 0, [cls.mixed_attr_set.id])],
                "model_id": cls.variant_model_id,
            }
        )

        # Source and target products for template tests
        cls.source_tmpl = cls.env["product.template"].create(
            {
                "name": "Source Product",
                "attribute_set_id": cls.tmpl_attr_set.id,
            }
        )
        cls.target_tmpl_1 = cls.env["product.template"].create(
            {
                "name": "Target Product 1",
                "attribute_set_id": cls.tmpl_attr_set.id,
            }
        )
        cls.target_tmpl_2 = cls.env["product.template"].create(
            {
                "name": "Target Product 2",
                "attribute_set_id": cls.tmpl_attr_set.id,
            }
        )

    def _create_wizard(self, vals):
        return self.env["product.attribute.propagation.wizard"].create(vals)

    def test_propagate_template_all_types(self):
        """Test propagation of all attribute types, empty value overwrite, and chatter."""
        multi_options = self.attr_multi.option_ids[:2]
        self.source_tmpl.write(
            {
                "x_test_prop_char": "Test Value",
                "x_test_prop_bool": True,
                "x_test_prop_select": self.select_option_1.id,
                "x_test_prop_multi": [(6, 0, multi_options.ids)],
            }
        )
        # Pre-fill a target to verify overwrite
        self.target_tmpl_2.write({"x_test_prop_char": "Old Value"})
        msg_count_1 = len(self.target_tmpl_1.message_ids)
        msg_count_2 = len(self.target_tmpl_2.message_ids)
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [
                    (6, 0, [self.target_tmpl_1.id, self.target_tmpl_2.id])
                ],
            }
        )
        wizard.action_select_default_attributes()
        wizard.action_propagate()
        for target in (self.target_tmpl_1, self.target_tmpl_2):
            self.assertEqual(target.x_test_prop_char, "Test Value")
            self.assertTrue(target.x_test_prop_bool)
            self.assertEqual(target.x_test_prop_select, self.select_option_1)
            self.assertEqual(target.x_test_prop_multi, multi_options)
        # Chatter message posted on each target
        self.assertEqual(len(self.target_tmpl_1.message_ids), msg_count_1 + 1)
        self.assertEqual(len(self.target_tmpl_2.message_ids), msg_count_2 + 1)
        self.assertIn(
            self.source_tmpl.display_name,
            self.target_tmpl_1.message_ids[0].body,
        )
        # Empty value overwrite
        self.source_tmpl.write(
            {
                "x_test_prop_char": False,
                "x_test_prop_select": False,
                "x_test_prop_multi": [(5, 0)],
            }
        )
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [(6, 0, [self.target_tmpl_1.id])],
            }
        )
        wizard.action_select_default_attributes()
        wizard.action_propagate()
        self.assertFalse(self.target_tmpl_1.x_test_prop_char)
        self.assertFalse(self.target_tmpl_1.x_test_prop_select)
        self.assertFalse(self.target_tmpl_1.x_test_prop_multi)

    def test_propagate_variant_attributes(self):
        """Test propagation between product.product records."""
        source_variant = (
            self.env["product.template"]
            .create(
                {
                    "name": "Source Variant Product",
                    "attribute_set_id": self.variant_attr_set.id,
                }
            )
            .product_variant_id
        )
        target_variant = (
            self.env["product.template"]
            .create(
                {
                    "name": "Target Variant Product",
                    "attribute_set_id": self.variant_attr_set.id,
                }
            )
            .product_variant_id
        )
        source_variant.write({"x_test_prop_v_char": "Variant Value"})
        wizard = self._create_wizard(
            {
                "propagation_model": "product.product",
                "source_product_id": source_variant.id,
                "target_product_ids": [(6, 0, [target_variant.id])],
            }
        )
        wizard.action_select_default_attributes()
        wizard.action_propagate()
        self.assertEqual(target_variant.x_test_prop_v_char, "Variant Value")

    def test_propagate_filters_by_model(self):
        """Test that only attributes matching the propagation model are propagated."""
        (self.source_tmpl | self.target_tmpl_1).write(
            {"attribute_set_id": self.mixed_attr_set.id}
        )
        source_variant = self.source_tmpl.product_variant_id
        target_variant = self.target_tmpl_1.product_variant_id
        self.source_tmpl.write({"x_test_prop_mixed_t": "Tmpl Value"})
        source_variant.write({"x_test_prop_mixed_v": "Variant Value"})
        # Propagate as product.template: only template attr should be copied
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [(6, 0, [self.target_tmpl_1.id])],
            }
        )
        wizard.action_select_default_attributes()
        wizard.action_propagate()
        self.assertEqual(self.target_tmpl_1.x_test_prop_mixed_t, "Tmpl Value")
        self.assertFalse(target_variant.x_test_prop_mixed_v)

    def test_error_no_targets(self):
        """Test UserError when no targets are selected."""
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_propagate()

    def test_error_no_attribute_set(self):
        """Test UserError when source has no attribute set."""
        self.source_tmpl.attribute_set_id = False
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [(6, 0, [self.target_tmpl_1.id])],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_propagate()

    def test_has_propagatable_attributes_template(self):
        """Test computed field on product.template."""
        self.assertTrue(self.source_tmpl.has_propagatable_attributes)
        self.source_tmpl.attribute_set_id = False
        self.assertFalse(self.source_tmpl.has_propagatable_attributes)

    def test_has_propagatable_attributes_variant(self):
        """Test computed field on product.product."""
        variant = self.source_tmpl.product_variant_id
        # tmpl_attr_set has only product.template attributes
        self.assertFalse(variant.has_propagatable_attributes)
        self.source_tmpl.attribute_set_id = self.variant_attr_set
        self.assertTrue(variant.has_propagatable_attributes)

    def test_compute_attribute_set_id(self):
        """Test wizard computed attribute_set_id field."""
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
            }
        )
        self.assertEqual(wizard.attribute_set_id, self.tmpl_attr_set)

    def test_default_is_propagated_default_value(self):
        """Test that default_is_propagated is True by default on attributes."""
        self.assertTrue(self.attr_char.default_is_propagated)
        self.assertTrue(self.attr_bool.default_is_propagated)
        self.assertTrue(self.attr_select.default_is_propagated)
        self.assertTrue(self.attr_multi.default_is_propagated)

    def test_wizard_attribute_ids_empty_on_open(self):
        """Wizard opens with no attributes selected to propagate."""
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
            }
        )
        expected_available = (
            self.attr_char | self.attr_bool | self.attr_select | self.attr_multi
        )
        self.assertEqual(wizard.available_attribute_ids, expected_available)
        self.assertFalse(wizard.attribute_ids)

    def test_wizard_select_default_attributes(self):
        """The action prefills attributes with default_is_propagated=True."""
        self.attr_bool.default_is_propagated = False
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
            }
        )
        wizard.action_select_default_attributes()
        self.assertEqual(
            wizard.attribute_ids,
            self.attr_char | self.attr_select | self.attr_multi,
        )

    def test_wizard_clear_attributes(self):
        """The clear action deselects all attributes."""
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
            }
        )
        wizard.action_select_default_attributes()
        self.assertTrue(wizard.attribute_ids)
        wizard.action_clear_attributes()
        self.assertFalse(wizard.attribute_ids)

    def test_wizard_attribute_ids_filters_propagation(self):
        """Only selected attributes are propagated; deselected ones are skipped."""
        self.source_tmpl.write(
            {
                "x_test_prop_char": "Char Value",
                "x_test_prop_bool": True,
            }
        )
        self.target_tmpl_1.write({"x_test_prop_char": "Old Char"})
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [(6, 0, [self.target_tmpl_1.id])],
            }
        )
        wizard.attribute_ids = self.attr_bool
        wizard.action_propagate()
        self.assertEqual(self.target_tmpl_1.x_test_prop_char, "Old Char")
        self.assertTrue(self.target_tmpl_1.x_test_prop_bool)

    def test_error_no_attributes_selected(self):
        """UserError when user deselects all attributes."""
        wizard = self._create_wizard(
            {
                "propagation_model": "product.template",
                "source_product_tmpl_id": self.source_tmpl.id,
                "target_product_tmpl_ids": [(6, 0, [self.target_tmpl_1.id])],
            }
        )
        wizard.attribute_ids = [(5, 0)]
        with self.assertRaises(UserError):
            wizard.action_propagate()
