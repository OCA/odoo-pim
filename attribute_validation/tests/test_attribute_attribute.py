"""Tests for attribute.attribute extension."""

from odoo.tests.common import TransactionCase


class TestAttributeAttribute(TransactionCase):
    """Test cases for attribute.attribute validation extension."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.Attribute = cls.env["attribute.attribute"]
        cls.Rule = cls.env["attribute.validation.rule"]
        cls.AllowedValue = cls.env["attribute.validation.allowed.value"]
        cls.product_model = cls.env.ref("product.model_product_template")
        cls.validation_group = cls.env["attribute.group"].create(
            {"name": "Validation Test Group", "model_id": cls.product_model.id}
        )

    def test_validate_value_single_rule(self):
        """Test validation with a single rule."""
        rule = self.Rule.create(
            {
                "name": "Year Rule",
                "validation_type": "range",
                "range_min": 1950,
                "range_max": 2030,
            }
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_year",
                "field_description": "Test Year",
                "attribute_type": "integer",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule.id)],
            }
        )

        is_valid, errors = attribute.validate_value(2020)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        is_valid, errors = attribute.validate_value(1900)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)

        # Cleanup
        attribute.unlink()
        rule.unlink()

    def test_validate_value_multiple_rules(self):
        """Test validation with multiple rules (all must pass)."""
        rule1 = self.Rule.create(
            {
                "name": "Range Rule",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 100,
            }
        )
        rule2 = self.Rule.create(
            {
                "name": "Even Rule",
                "validation_type": "python",
                "python_code": "int(value) % 2 == 0",
            }
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_multi",
                "field_description": "Test Multi",
                "attribute_type": "integer",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule1.id), (4, rule2.id)],
            }
        )

        # Valid: in range and even
        is_valid, errors = attribute.validate_value(50)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid: in range but odd
        is_valid, errors = attribute.validate_value(51)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)

        # Invalid: even but out of range
        is_valid, errors = attribute.validate_value(200)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)

        # Invalid: out of range and odd
        is_valid, errors = attribute.validate_value(201)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 2)

        # Cleanup
        attribute.unlink()
        rule1.unlink()
        rule2.unlink()

    def test_validate_value_inactive_rules(self):
        """Test that inactive rules are skipped."""
        rule = self.Rule.create(
            {
                "name": "Inactive Rule",
                "validation_type": "regex",
                "regex_pattern": r"^NEVER$",
                "active": False,
            }
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_inactive",
                "field_description": "Test Inactive",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule.id)],
            }
        )

        # Should pass because rule is inactive
        is_valid, errors = attribute.validate_value("anything")
        self.assertTrue(is_valid)

        # Cleanup
        attribute.unlink()
        rule.unlink()

    def test_get_autocomplete_values(self):
        """Test autocomplete aggregation from multiple rules."""
        rule1 = self.Rule.create(
            {
                "name": "Colors",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create(
            [
                {"rule_id": rule1.id, "value": "red"},
                {"rule_id": rule1.id, "value": "blue"},
            ]
        )

        rule2 = self.Rule.create(
            {
                "name": "More Colors",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create(
            [
                {"rule_id": rule2.id, "value": "green"},
                {"rule_id": rule2.id, "value": "yellow"},
            ]
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_autocomplete",
                "field_description": "Test Autocomplete",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule1.id), (4, rule2.id)],
                "enable_autocomplete": True,
            }
        )

        results = attribute.get_autocomplete_values("", limit=10)
        self.assertEqual(len(results), 4)
        values = [r["value"] for r in results]
        self.assertIn("red", values)
        self.assertIn("blue", values)
        self.assertIn("green", values)
        self.assertIn("yellow", values)

        # Cleanup
        attribute.unlink()
        rule1.unlink()
        rule2.unlink()

    def test_get_autocomplete_disabled(self):
        """Test autocomplete returns empty when disabled."""
        rule = self.Rule.create(
            {
                "name": "Test Rule",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create({"rule_id": rule.id, "value": "test"})

        attribute = self.Attribute.create(
            {
                "name": "x_test_disabled",
                "field_description": "Test Disabled",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule.id)],
                "enable_autocomplete": False,
            }
        )

        results = attribute.get_autocomplete_values("", limit=10)
        self.assertEqual(len(results), 0)

        # Cleanup
        attribute.unlink()
        rule.unlink()

    def test_get_autocomplete_deduplication(self):
        """Test that duplicate values are removed from autocomplete."""
        rule1 = self.Rule.create(
            {
                "name": "Rule 1",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create({"rule_id": rule1.id, "value": "duplicate"})

        rule2 = self.Rule.create(
            {
                "name": "Rule 2",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create({"rule_id": rule2.id, "value": "duplicate"})

        attribute = self.Attribute.create(
            {
                "name": "x_test_dedup",
                "field_description": "Test Dedup",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule1.id), (4, rule2.id)],
                "enable_autocomplete": True,
            }
        )

        results = attribute.get_autocomplete_values("", limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["value"], "duplicate")

        # Cleanup
        attribute.unlink()
        rule1.unlink()
        rule2.unlink()

    def test_get_cascade_effects(self):
        """Test getting cascade effects from attribute."""
        brand_attr = self.Attribute.create(
            {
                "name": "x_test_brand_cascade",
                "field_description": "Test Brand Cascade",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
            }
        )
        engine_attr = self.Attribute.create(
            {
                "name": "x_test_engine_cascade",
                "field_description": "Test Engine Cascade",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
            }
        )

        cascade = self.env["attribute.validation.cascade"].create(
            {
                "name": "Test Cascade",
                "trigger_attribute_id": brand_attr.id,
                "trigger_operator": "=",
                "trigger_value": "CAT",
                "target_attribute_id": engine_attr.id,
                "effect_type": "required",
            }
        )

        effects = brand_attr.get_cascade_effects("CAT")
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0]["effect_type"], "required")

        effects = brand_attr.get_cascade_effects("Other")
        self.assertEqual(len(effects), 0)

        # Cleanup
        cascade.unlink()
        engine_attr.unlink()
        brand_attr.unlink()

    def test_validation_rule_count(self):
        """Test validation rule count computation."""
        rule1 = self.Rule.create(
            {
                "name": "Rule 1",
                "validation_type": "regex",
                "regex_pattern": ".*",
            }
        )
        rule2 = self.Rule.create(
            {
                "name": "Rule 2",
                "validation_type": "regex",
                "regex_pattern": ".*",
            }
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_count",
                "field_description": "Test Count",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
            }
        )

        self.assertEqual(attribute.validation_rule_count, 0)

        attribute.write({"validation_rule_ids": [(4, rule1.id)]})
        attribute.invalidate_recordset()
        self.assertEqual(attribute.validation_rule_count, 1)

        attribute.write({"validation_rule_ids": [(4, rule2.id)]})
        attribute.invalidate_recordset()
        self.assertEqual(attribute.validation_rule_count, 2)

        # Cleanup
        attribute.unlink()
        rule1.unlink()
        rule2.unlink()

    def test_action_view_validation_rules(self):
        """Test action to view validation rules."""
        rule = self.Rule.create(
            {
                "name": "Test Rule",
                "validation_type": "regex",
                "regex_pattern": ".*",
            }
        )

        attribute = self.Attribute.create(
            {
                "name": "x_test_action",
                "field_description": "Test Action",
                "attribute_type": "char",
                "model_id": self.product_model.id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule.id)],
            }
        )

        action = attribute.action_view_validation_rules()
        self.assertEqual(action["res_model"], "attribute.validation.rule")
        self.assertIn(rule.id, action["domain"][0][2])

        # Cleanup
        attribute.unlink()
        rule.unlink()
