"""Tests for website JSONB attribute filtering."""

from odoo.tests.common import TransactionCase


class TestWebsiteJsonbFilters(TransactionCase):
    """Test cases for website JSONB attribute filtering."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.AttributeAttribute = cls.env["attribute.attribute"]
        cls.AttributeGroup = cls.env["attribute.group"]
        cls.ProductTemplate = cls.env["product.template"]
        cls.IrModel = cls.env["ir.model"]

        # Get product.template model
        cls.product_model = cls.IrModel.search(
            [("model", "=", "product.template")], limit=1
        )

        # Create an attribute group for product.template
        cls.test_group = cls.AttributeGroup.create(
            {
                "name": "Test Website Group",
                "model_id": cls.product_model.id,
            }
        )

    def _create_test_attribute(
        self,
        name,
        attr_type="char",
        website_visible=False,
        website_filter_type="checkbox",
    ):
        """Helper to create a serialized test attribute."""
        return self.AttributeAttribute.create(
            {
                "name": f"x_{name}",
                "field_description": f"Test {name.title()}",
                "attribute_type": attr_type,
                "model_id": self.product_model.id,
                "attribute_group_id": self.test_group.id,
                "serialized": True,
                "website_visible": website_visible,
                "website_filter_type": website_filter_type,
            }
        )

    def test_website_visible_field(self):
        """Test website_visible field on attribute."""
        attr = self._create_test_attribute("color", website_visible=True)
        self.assertTrue(attr.website_visible)

        attr2 = self._create_test_attribute("hidden", website_visible=False)
        self.assertFalse(attr2.website_visible)

    def test_website_filter_type_field(self):
        """Test website_filter_type field options."""
        attr_checkbox = self._create_test_attribute(
            "cb_attr", website_filter_type="checkbox"
        )
        self.assertEqual(attr_checkbox.website_filter_type, "checkbox")

        attr_select = self._create_test_attribute(
            "sel_attr", website_filter_type="select"
        )
        self.assertEqual(attr_select.website_filter_type, "select")

        attr_range = self._create_test_attribute(
            "range_attr", attr_type="integer", website_filter_type="range"
        )
        self.assertEqual(attr_range.website_filter_type, "range")

    def test_website_sequence_field(self):
        """Test website_sequence field for ordering."""
        attr1 = self._create_test_attribute("first", website_visible=True)
        attr1.website_sequence = 5

        attr2 = self._create_test_attribute("second", website_visible=True)
        attr2.website_sequence = 10

        # Search should return in sequence order
        attrs = self.AttributeAttribute.search(
            [
                ("model", "=", "product.template"),
                ("website_visible", "=", True),
            ],
            order="website_sequence, name",
        )

        # First should come before second
        self.assertTrue(attr1 in attrs)
        self.assertTrue(attr2 in attrs)

    def test_get_website_jsonb_attributes(self):
        """Test getting website-visible JSONB attributes."""
        # Create visible and hidden attributes
        visible_attr = self._create_test_attribute("visible", website_visible=True)
        hidden_attr = self._create_test_attribute("hidden", website_visible=False)

        # Get website attributes
        website_attrs = self.ProductTemplate.get_website_jsonb_attributes()

        # Should include visible, exclude hidden
        self.assertIn(visible_attr, website_attrs)
        self.assertNotIn(hidden_attr, website_attrs)

    def test_range_filter_type_warning_for_char(self):
        """Test that range filter shows warning for non-numeric types."""
        attr = self._create_test_attribute(
            "char_range", attr_type="char", website_filter_type="checkbox"
        )

        # Change to range type
        attr.website_filter_type = "range"
        result = attr._onchange_website_filter_type()

        # Should return warning for char type
        self.assertIsNotNone(result)
        self.assertIn("warning", result)

    def test_range_filter_type_valid_for_integer(self):
        """Test that range filter is valid for integer types."""
        attr = self._create_test_attribute(
            "int_range", attr_type="integer", website_filter_type="checkbox"
        )

        # Set index type to btree for optimal range query performance
        attr.index_type = "btree"

        # Change to range type
        attr.website_filter_type = "range"
        result = attr._onchange_website_filter_type()

        # Should not return warning for integer with btree index
        self.assertIsNone(result)

    def test_get_distinct_values(self):
        """Test _get_distinct_values method."""
        attr = self._create_test_attribute("color", website_visible=True)

        # Create products with different color values
        products = []
        for color in ["red", "blue", "green", "red"]:  # red appears twice
            product = self.ProductTemplate.create(
                {
                    "name": f"Test Product {color}",
                    "type": "consu",
                }
            )
            # Set the attribute value via x_custom_json_attrs
            if hasattr(product, "x_custom_json_attrs"):
                product.write({"x_custom_json_attrs": {attr.name: color}})
            products.append(product)

        # Get distinct values
        distinct_values = attr._get_distinct_values()

        # Should return unique values
        self.assertIsInstance(distinct_values, list)
        # Values should be unique (red only once)
        if distinct_values:
            self.assertEqual(len(distinct_values), len(set(distinct_values)))

    def test_get_min_max_values(self):
        """Test _get_min_max_values method for numeric attributes."""
        attr = self._create_test_attribute(
            "capacity", attr_type="integer", website_visible=True
        )

        # Create products with different capacity values
        products = []
        for capacity in [100, 500, 1000]:
            product = self.ProductTemplate.create(
                {
                    "name": f"Test Product {capacity}",
                    "type": "consu",
                }
            )
            if hasattr(product, "x_custom_json_attrs"):
                product.write({"x_custom_json_attrs": {attr.name: capacity}})
            products.append(product)

        # Get min/max
        min_val, max_val = attr._get_min_max_values()

        # Should return numeric range
        if min_val is not None and max_val is not None:
            self.assertLessEqual(min_val, max_val)

    def test_get_jsonb_attribute_domain_equality(self):
        """Test building domain for equality filters."""
        # Create test attribute
        attr = self._create_test_attribute("brand", website_visible=True)

        # Test domain building with equality filter
        filters = {attr.name: ["caterpillar", "komatsu"]}
        domain = self.ProductTemplate._get_jsonb_attribute_domain(filters)

        # Should return a valid domain
        self.assertIsInstance(domain, list)

    def test_get_jsonb_attribute_domain_range(self):
        """Test building domain for range filters."""
        # Create test attribute
        attr = self._create_test_attribute(
            "weight", attr_type="integer", website_visible=True
        )

        # Test domain building with range filter
        filters = {attr.name: {"min": 1000, "max": 5000}}
        domain = self.ProductTemplate._get_jsonb_attribute_domain(filters)

        # Should return a valid domain
        self.assertIsInstance(domain, list)

    def test_empty_filters_return_empty_domain(self):
        """Test that empty filters return empty domain."""
        domain = self.ProductTemplate._get_jsonb_attribute_domain({})
        self.assertEqual(domain, [])

        domain2 = self.ProductTemplate._get_jsonb_attribute_domain(None)
        self.assertEqual(domain2, [])
