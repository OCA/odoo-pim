"""Tests for attribute.validation.cascade model."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAttributeValidationCascade(TransactionCase):
    """Test cases for cascading validation rules."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.Cascade = cls.env["attribute.validation.cascade"]
        cls.Rule = cls.env["attribute.validation.rule"]
        cls.Attribute = cls.env["attribute.attribute"]
        cls.product_model = cls.env.ref("product.model_product_template")
        cls.validation_group = cls.env["attribute.group"].create(
            {"name": "Validation Test Group", "model_id": cls.product_model.id}
        )

        # Create test attributes
        cls.brand_attr = cls.Attribute.create(
            {
                "name": "x_test_brand",
                "field_description": "Test Brand",
                "attribute_type": "char",
                "model_id": cls.product_model.id,
                "attribute_group_id": cls.validation_group.id,
            }
        )
        cls.engine_attr = cls.Attribute.create(
            {
                "name": "x_test_engine",
                "field_description": "Test Engine",
                "attribute_type": "char",
                "model_id": cls.product_model.id,
                "attribute_group_id": cls.validation_group.id,
            }
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        cls.brand_attr.unlink()
        cls.engine_attr.unlink()
        super().tearDownClass()

    def test_cascade_equals_operator(self):
        """Test cascade with equals operator."""
        cascade = self.Cascade.create(
            {
                "name": "Brand requires engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
            }
        )

        # Should apply when value equals
        should_apply, effect = cascade.evaluate("CAT")
        self.assertTrue(should_apply)
        self.assertEqual(effect["effect_type"], "required")
        self.assertEqual(effect["target_attribute_id"], self.engine_attr.id)

        # Should not apply when value differs
        should_apply, effect = cascade.evaluate("Komatsu")
        self.assertFalse(should_apply)
        self.assertEqual(effect, {})

    def test_cascade_not_equals_operator(self):
        """Test cascade with not equals operator."""
        cascade = self.Cascade.create(
            {
                "name": "Non-CAT hides engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "!=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "hidden",
            }
        )

        should_apply, effect = cascade.evaluate("Komatsu")
        self.assertTrue(should_apply)
        self.assertEqual(effect["effect_type"], "hidden")

        should_apply, _ = cascade.evaluate("CAT")
        self.assertFalse(should_apply)

    def test_cascade_in_operator(self):
        """Test cascade with in operator."""
        cascade = self.Cascade.create(
            {
                "name": "US brands require engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "in",
                "trigger_value": "CAT, John Deere, Case",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
            }
        )

        should_apply, _ = cascade.evaluate("CAT")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("John Deere")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("Case")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("Komatsu")
        self.assertFalse(should_apply)

    def test_cascade_not_in_operator(self):
        """Test cascade with not in operator."""
        cascade = self.Cascade.create(
            {
                "name": "Non-US brands hide engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "not in",
                "trigger_value": "CAT, John Deere",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "hidden",
            }
        )

        should_apply, _ = cascade.evaluate("Komatsu")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("CAT")
        self.assertFalse(should_apply)

    def test_cascade_set_operator(self):
        """Test cascade with set (not empty) operator."""
        cascade = self.Cascade.create(
            {
                "name": "Brand set requires engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "set",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
            }
        )

        should_apply, _ = cascade.evaluate("Any Value")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("")
        self.assertFalse(should_apply)

        should_apply, _ = cascade.evaluate(None)
        self.assertFalse(should_apply)

        should_apply, _ = cascade.evaluate(False)
        self.assertFalse(should_apply)

    def test_cascade_not_set_operator(self):
        """Test cascade with not_set (empty) operator."""
        cascade = self.Cascade.create(
            {
                "name": "No brand hides engine",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "not_set",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "hidden",
            }
        )

        should_apply, _ = cascade.evaluate("")
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate(None)
        self.assertTrue(should_apply)

        should_apply, _ = cascade.evaluate("Some Value")
        self.assertFalse(should_apply)

    def test_cascade_apply_rule_effect(self):
        """Test cascade that applies a validation rule."""
        rule = self.Rule.create(
            {
                "name": "CAT Engine Rule",
                "validation_type": "regex",
                "regex_pattern": r"^CAT-[0-9]+$",
            }
        )

        cascade = self.Cascade.create(
            {
                "name": "CAT applies engine rule",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "apply_rule",
                "validation_rule_id": rule.id,
            }
        )

        should_apply, effect = cascade.evaluate("CAT")
        self.assertTrue(should_apply)
        self.assertEqual(effect["effect_type"], "apply_rule")
        self.assertEqual(effect["validation_rule_id"], rule.id)

    def test_cascade_filter_values_effect(self):
        """Test cascade that filters allowed values."""
        cascade = self.Cascade.create(
            {
                "name": "CAT filters engines",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "filter_values",
                "allowed_values_filter": "C7, C9, C13, C15",
            }
        )

        should_apply, effect = cascade.evaluate("CAT")
        self.assertTrue(should_apply)
        self.assertEqual(effect["effect_type"], "filter_values")
        self.assertEqual(effect["allowed_values"], ["C7", "C9", "C13", "C15"])

    def test_cascade_filter_domain_with_placeholder(self):
        """Test cascade filter domain with trigger value placeholder."""
        cascade = self.Cascade.create(
            {
                "name": "Brand filters by brand",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "set",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "filter_values",
                "filter_domain": "[('brand', '=', '{trigger_value}')]",
            }
        )

        should_apply, effect = cascade.evaluate("CAT")
        self.assertTrue(should_apply)
        self.assertEqual(effect["filter_domain"], "[('brand', '=', 'CAT')]")

    def test_cascade_constraint_different_attributes(self):
        """Test that trigger and target must be different."""
        with self.assertRaises(ValidationError):
            self.Cascade.create(
                {
                    "name": "Self Reference",
                    "trigger_attribute_id": self.brand_attr.id,
                    "trigger_operator": "=",
                    "trigger_value": "X",
                    "target_attribute_id": self.brand_attr.id,
                    "effect_type": "required",
                }
            )

    def test_get_cascade_effects_for_attribute(self):
        """Test getting all cascade effects for an attribute."""
        self.Cascade.create(
            {
                "name": "Cascade 1",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
            }
        )
        self.Cascade.create(
            {
                "name": "Cascade 2",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "visible",
            }
        )

        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "CAT"
        )
        self.assertEqual(len(effects), 2)
        effect_types = [e["effect_type"] for e in effects]
        self.assertIn("required", effect_types)
        self.assertIn("visible", effect_types)

        # Different value should not trigger
        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "Komatsu"
        )
        self.assertEqual(len(effects), 0)

    def test_cascade_attribute_set_scope(self):
        """Test cascade scoped to specific attribute sets."""
        attr_set = self.env["attribute.set"].create(
            {
                "name": "Test Set",
                "model_id": self.product_model.id,
            }
        )

        cascade = self.Cascade.create(
            {
                "name": "Scoped Cascade",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
                "attribute_set_ids": [(4, attr_set.id)],
            }
        )

        # Should apply for matching attribute set
        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "CAT", attribute_set_id=attr_set.id
        )
        self.assertEqual(len(effects), 1)

        # Should not apply for different attribute set
        other_set = self.env["attribute.set"].create(
            {
                "name": "Other Set",
                "model_id": self.product_model.id,
            }
        )
        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "CAT", attribute_set_id=other_set.id
        )
        self.assertEqual(len(effects), 0)

        # Should apply when no set specified (cascade has scope)
        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "CAT", attribute_set_id=None
        )
        self.assertEqual(len(effects), 1)

        # Cleanup
        cascade.unlink()
        attr_set.unlink()
        other_set.unlink()

    def test_cascade_inactive(self):
        """Test that inactive cascades are not applied."""
        cascade = self.Cascade.create(
            {
                "name": "Inactive Cascade",
                "trigger_attribute_id": self.brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": self.engine_attr.id,
                "effect_type": "required",
                "active": False,
            }
        )

        effects = self.Cascade.get_cascade_effects_for_attribute(
            self.brand_attr.id, "CAT"
        )
        self.assertEqual(len(effects), 0)

        # Cleanup
        cascade.unlink()
