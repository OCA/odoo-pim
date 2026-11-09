"""Tests for attribute.validation.rule model."""

from odoo.tests.common import TransactionCase


class TestAttributeValidationRule(TransactionCase):
    """Test cases for validation rule types."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.Rule = cls.env["attribute.validation.rule"]
        cls.AllowedValue = cls.env["attribute.validation.allowed.value"]
        cls.product_model = cls.env.ref("product.model_product_template")
        cls.validation_group = cls.env["attribute.group"].create(
            {"name": "Validation Test Group", "model_id": cls.product_model.id}
        )

    def test_regex_validation_basic(self):
        """Test basic regex pattern validation."""
        rule = self.Rule.create(
            {
                "name": "Test Regex",
                "validation_type": "regex",
                "regex_pattern": r"^[A-Z]{3}[0-9]{3}$",
            }
        )

        # Valid values
        is_valid, error = rule.validate("ABC123")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        is_valid, error = rule.validate("XYZ999")
        self.assertTrue(is_valid)

        # Invalid values
        is_valid, error = rule.validate("abc123")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

        is_valid, error = rule.validate("ABCD1234")
        self.assertFalse(is_valid)

        is_valid, error = rule.validate("AB123")
        self.assertFalse(is_valid)

    def test_regex_validation_case_insensitive(self):
        """Test regex with case insensitive flag."""
        rule = self.Rule.create(
            {
                "name": "Test Regex CI",
                "validation_type": "regex",
                "regex_pattern": r"^[A-Z]{3}[0-9]{3}$",
                "regex_flags": "ignorecase",
            }
        )

        is_valid, _ = rule.validate("ABC123")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("abc123")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("AbC123")
        self.assertTrue(is_valid)

    def test_allowed_values_validation(self):
        """Test static allowed values validation."""
        rule = self.Rule.create(
            {
                "name": "Test Allowed",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create(
            [
                {"rule_id": rule.id, "value": "red"},
                {"rule_id": rule.id, "value": "green"},
                {"rule_id": rule.id, "value": "blue"},
            ]
        )

        # Valid values
        is_valid, _ = rule.validate("red")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("green")
        self.assertTrue(is_valid)

        # Invalid values
        is_valid, error = rule.validate("yellow")
        self.assertFalse(is_valid)
        self.assertIn("yellow", error)

        is_valid, _ = rule.validate("RED")
        self.assertFalse(is_valid)  # Case sensitive by default

    def test_allowed_values_inactive(self):
        """Test that inactive allowed values are not accepted."""
        rule = self.Rule.create(
            {
                "name": "Test Allowed Inactive",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create(
            [
                {"rule_id": rule.id, "value": "active_val", "active": True},
                {"rule_id": rule.id, "value": "inactive_val", "active": False},
            ]
        )

        is_valid, _ = rule.validate("active_val")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("inactive_val")
        self.assertFalse(is_valid)

    def test_range_validation_inclusive(self):
        """Test numeric range validation with inclusive boundaries."""
        rule = self.Rule.create(
            {
                "name": "Test Range",
                "validation_type": "range",
                "range_min": 1950,
                "range_max": 2030,
                "range_min_inclusive": True,
                "range_max_inclusive": True,
            }
        )

        # Valid values
        is_valid, _ = rule.validate(2020)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("2020")  # String should work
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(1950)  # Min boundary
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(2030)  # Max boundary
        self.assertTrue(is_valid)

        # Invalid values
        is_valid, error = rule.validate(1949)
        self.assertFalse(is_valid)

        is_valid, _ = rule.validate(2031)
        self.assertFalse(is_valid)

    def test_range_validation_exclusive(self):
        """Test numeric range validation with exclusive boundaries."""
        rule = self.Rule.create(
            {
                "name": "Test Range Exclusive",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 100,
                "range_min_inclusive": False,
                "range_max_inclusive": False,
            }
        )

        is_valid, _ = rule.validate(50)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(0)  # Exclusive, so 0 is invalid
        self.assertFalse(is_valid)

        is_valid, _ = rule.validate(100)  # Exclusive, so 100 is invalid
        self.assertFalse(is_valid)

        is_valid, _ = rule.validate(0.001)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(99.999)
        self.assertTrue(is_valid)

    def test_range_validation_with_step(self):
        """Test range validation with step constraint."""
        rule = self.Rule.create(
            {
                "name": "Test Range Step",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 100,
                "range_step": 5,
            }
        )

        # Valid values (multiples of 5)
        is_valid, _ = rule.validate(0)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(25)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(100)
        self.assertTrue(is_valid)

        # Invalid values (not multiples of 5)
        is_valid, _ = rule.validate(23)
        self.assertFalse(is_valid)

        is_valid, _ = rule.validate(7)
        self.assertFalse(is_valid)

    def test_range_validation_fractional_step(self):
        """Decimal increments must be accepted. Regression: 0.3 with step 0.1
        gives 0.3 % 0.1 == 0.0999… so the old one-sided ``> 0.0001`` tolerance
        wrongly rejected most tenths."""
        rule = self.Rule.create(
            {
                "name": "Test Fractional Step",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 10,
                "range_step": 0.1,
            }
        )
        for value in (0.1, 0.3, 0.7, 1.2, 9.9):
            is_valid, _ = rule.validate(value)
            self.assertTrue(is_valid, f"{value} should be a valid 0.1 increment")
        for value in (0.35, 0.05, 1.23):
            is_valid, _ = rule.validate(value)
            self.assertFalse(is_valid, f"{value} should be off-grid for step 0.1")

    def test_range_validation_non_numeric(self):
        """Test range validation rejects non-numeric values."""
        rule = self.Rule.create(
            {
                "name": "Test Range Non-Numeric",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 100,
            }
        )

        is_valid, error = rule.validate("abc")
        self.assertFalse(is_valid)
        self.assertIn("not a valid number", error)

    def test_python_validation(self):
        """Test Python expression validation."""
        # Even number check
        rule = self.Rule.create(
            {
                "name": "Test Python Even",
                "validation_type": "python",
                "python_code": "int(value) % 2 == 0",
            }
        )

        is_valid, _ = rule.validate(2)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(4)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(3)
        self.assertFalse(is_valid)

    def test_python_validation_with_string(self):
        """Test Python expression with string operations."""
        rule = self.Rule.create(
            {
                "name": "Test Python String",
                "validation_type": "python",
                "python_code": "value.startswith('PREFIX_')",
            }
        )

        is_valid, _ = rule.validate("PREFIX_test")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("test")
        self.assertFalse(is_valid)

    def test_dynamic_source_validation(self):
        """Test dynamic source validation from another model."""
        # Use res.country as source
        rule = self.Rule.create(
            {
                "name": "Test Dynamic Country",
                "validation_type": "dynamic_source",
                "source_model_id": self.env.ref("base.model_res_country").id,
                "source_field": "code",
                "source_domain": "[]",
                "cache_timeout": 0,  # No cache for testing
            }
        )

        # NL should exist
        is_valid, _ = rule.validate("NL")
        self.assertTrue(is_valid)

        # US should exist
        is_valid, _ = rule.validate("US")
        self.assertTrue(is_valid)

        # XX should not exist
        is_valid, _ = rule.validate("XX")
        self.assertFalse(is_valid)

    def test_dynamic_source_with_domain(self):
        """Test dynamic source with filtering domain."""
        # Only get countries starting with 'N'
        rule = self.Rule.create(
            {
                "name": "Test Dynamic Filtered",
                "validation_type": "dynamic_source",
                "source_model_id": self.env.ref("base.model_res_country").id,
                "source_field": "code",
                "source_domain": "[('code', 'like', 'N%')]",
                "cache_timeout": 0,
            }
        )

        is_valid, _ = rule.validate("NL")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate("US")
        self.assertFalse(is_valid)

    def test_empty_value_passes(self):
        """Test that empty values pass validation (handled by required)."""
        rule = self.Rule.create(
            {
                "name": "Test Empty",
                "validation_type": "regex",
                "regex_pattern": r"^[A-Z]+$",
            }
        )

        is_valid, _ = rule.validate("")
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(None)
        self.assertTrue(is_valid)

        is_valid, _ = rule.validate(False)
        self.assertTrue(is_valid)

    def test_zero_value_validates(self):
        """Test that zero is validated (not treated as empty)."""
        rule = self.Rule.create(
            {
                "name": "Test Zero",
                "validation_type": "range",
                "range_min": 0,
                "range_max": 100,
            }
        )

        is_valid, _ = rule.validate(0)
        self.assertTrue(is_valid)

    def test_custom_error_message(self):
        """Test custom error message with placeholder."""
        rule = self.Rule.create(
            {
                "name": "Test Custom Error",
                "validation_type": "regex",
                "regex_pattern": r"^[A-Z]+$",
                "error_message": "'{value}' must contain only uppercase letters",
            }
        )

        is_valid, error = rule.validate("abc123")
        self.assertFalse(is_valid)
        self.assertIn("abc123", error)
        self.assertIn("uppercase letters", error)

    def test_autocomplete_allowed_values(self):
        """Test autocomplete for allowed values."""
        rule = self.Rule.create(
            {
                "name": "Test Autocomplete",
                "validation_type": "allowed_values",
            }
        )
        self.AllowedValue.create(
            [
                {"rule_id": rule.id, "value": "apple", "display_value": "Apple Fruit"},
                {"rule_id": rule.id, "value": "apricot"},
                {"rule_id": rule.id, "value": "banana"},
            ]
        )

        # Search for 'ap'
        results = rule.get_autocomplete_values("ap", limit=10)
        self.assertEqual(len(results), 2)
        values = [r["value"] for r in results]
        self.assertIn("apple", values)
        self.assertIn("apricot", values)
        self.assertNotIn("banana", values)

        # Check display name
        apple_result = next(r for r in results if r["value"] == "apple")
        self.assertEqual(apple_result["display"], "Apple Fruit")

    def test_autocomplete_range_with_step(self):
        """Test autocomplete for range with step."""
        rule = self.Rule.create(
            {
                "name": "Test Autocomplete Range",
                "validation_type": "range",
                "range_min": 2020,
                "range_max": 2025,
                "range_step": 1,
            }
        )

        results = rule.get_autocomplete_values("", limit=10)
        self.assertEqual(len(results), 6)  # 2020-2025 inclusive
        values = [r["value"] for r in results]
        self.assertIn("2020", values)
        self.assertIn("2025", values)

    def test_validate_batch(self):
        """Test batch validation for efficiency."""
        rule = self.Rule.create(
            {
                "name": "Test Batch",
                "validation_type": "dynamic_source",
                "source_model_id": self.env.ref("base.model_res_country").id,
                "source_field": "code",
                "cache_timeout": 0,
            }
        )

        values = ["NL", "US", "XX", "DE", "YY"]
        results = rule.validate_batch(values)

        self.assertEqual(len(results), 5)
        self.assertTrue(results["NL"][0])
        self.assertTrue(results["US"][0])
        self.assertFalse(results["XX"][0])
        self.assertTrue(results["DE"][0])
        self.assertFalse(results["YY"][0])

    def test_usage_count(self):
        """Test usage count computation."""
        rule = self.Rule.create(
            {
                "name": "Test Usage",
                "validation_type": "regex",
                "regex_pattern": r".*",
            }
        )

        self.assertEqual(rule.usage_count, 0)

        # Create an attribute and link the rule
        attribute = self.env["attribute.attribute"].create(
            {
                "name": "x_test_usage",
                "field_description": "Test Usage",
                "attribute_type": "char",
                "model_id": self.env.ref("product.model_product_template").id,
                "attribute_group_id": self.validation_group.id,
                "validation_rule_ids": [(4, rule.id)],
            }
        )

        rule.invalidate_recordset()
        self.assertEqual(rule.usage_count, 1)

        # Cleanup
        attribute.unlink()

    def test_cache_clear(self):
        """Test cache clearing for dynamic source."""
        rule = self.Rule.create(
            {
                "name": "Test Cache",
                "validation_type": "dynamic_source",
                "source_model_id": self.env.ref("base.model_res_country").id,
                "source_field": "code",
                "cache_timeout": 3600,
            }
        )

        # Trigger cache population
        rule._get_dynamic_values()

        # Clear cache
        result = rule.action_clear_cache()
        self.assertTrue(result)

        # Verify cache is cleared
        cache_key = rule._get_dynamic_values_cache_key()
        cached = self.env["ir.config_parameter"].sudo().get_param(cache_key)
        self.assertFalse(cached)
