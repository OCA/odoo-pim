"""Tests for B-tree expression indexes on serialized attributes."""

from odoo.tests.common import TransactionCase


class TestBtreeExpressionIndexes(TransactionCase):
    """Test cases for B-tree expression indexes on serialized attributes.

    These tests focus on the logic of the module without requiring actual
    JSONB columns in the database. Integration tests for actual index
    creation require a database with JSONB columns already configured.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.AttributeAttribute = cls.env["attribute.attribute"]
        cls.AttributeGroup = cls.env["attribute.group"]

        # Use res.partner model for testing
        cls.test_model = cls.env.ref("base.model_res_partner")

        # Create or get the serialization field
        cls.serialization_field = cls.env["ir.model.fields"].search(
            [
                ("model_id", "=", cls.test_model.id),
                ("name", "=", "x_custom_json_attrs"),
            ],
            limit=1,
        )
        if not cls.serialization_field:
            cls.serialization_field = cls.env["ir.model.fields"].create(
                {
                    "name": "x_custom_json_attrs",
                    "field_description": "Custom JSON Attributes",
                    "model_id": cls.test_model.id,
                    "ttype": "serialized",
                }
            )

        # Create an attribute group for testing
        cls.test_group = cls.AttributeGroup.create(
            {
                "name": "Test JSONB B-tree Group",
                "model_id": cls.test_model.id,
            }
        )

    def _attribute_vals(self, name, attr_type="integer", index_type="none"):
        """Helper returning the values of a serialized test attribute."""
        return {
            "name": f"x_{name}",
            "field_description": f"Test {name.title()}",
            "attribute_type": attr_type,
            "model_id": self.test_model.id,
            "attribute_group_id": self.test_group.id,
            "serialized": True,
            "serialization_field_id": self.serialization_field.id,
            "index_type": index_type,
        }

    def _create_numeric_attribute(self, name, attr_type="integer", index_type="none"):
        """Helper to create a serialized numeric test attribute."""
        return self.AttributeAttribute.create(
            self._attribute_vals(name, attr_type, index_type)
        )

    def _new_numeric_attribute(self, name, attr_type="integer", index_type="none"):
        """Helper to build an unsaved serialized numeric test attribute."""
        return self.AttributeAttribute.new(
            self._attribute_vals(name, attr_type, index_type)
        )

    def test_index_type_field_exists(self):
        """Test that index_type field exists on attribute."""
        attr = self._create_numeric_attribute("test_int")
        self.assertEqual(attr.index_type, "none")

    def test_btree_index_name_generation(self):
        """Test that B-tree index names are generated correctly."""
        attr = self._create_numeric_attribute("capacity")

        btree_index_name = attr._get_btree_index_name()

        self.assertIsNotNone(btree_index_name)
        self.assertTrue(btree_index_name.endswith("_btree"))

    def test_can_create_btree_index_for_supported_types(self):
        """Test _can_create_btree_index method for supported types."""
        int_attr = self._create_numeric_attribute("int_attr", "integer")
        float_attr = self._create_numeric_attribute("float_attr", "float")
        # date/datetime cannot be stored yet, so they are checked on a
        # virtual record: _can_create_btree_index only reads attribute_type.
        date_attr = self._new_numeric_attribute("date_attr", "date")
        datetime_attr = self._new_numeric_attribute("datetime_attr", "datetime")

        self.assertTrue(int_attr._can_create_btree_index())
        self.assertTrue(float_attr._can_create_btree_index())
        self.assertTrue(date_attr._can_create_btree_index())
        self.assertTrue(datetime_attr._can_create_btree_index())

    def test_cannot_create_btree_index_for_char(self):
        """Test _can_create_btree_index method for unsupported char type."""
        char_attr = self._create_numeric_attribute("char_attr", "char")

        self.assertFalse(char_attr._can_create_btree_index())

    def test_btree_index_not_created_for_unsupported_type(self):
        """Test that B-tree index creation is skipped for char attributes."""
        # Create attribute with btree index type but char attribute type
        attr = self._create_numeric_attribute("btree_char", "char", index_type="btree")

        # The index_type should be set as requested
        self.assertEqual(attr.index_type, "btree")

        # But no actual index should be created since char is not supported
        # (The _create_btree_expression_index method returns early)
        # We verify by checking the method returns False for unsupported types
        self.assertFalse(attr._can_create_btree_index())

    def test_index_type_onchange_sets_gin_flag(self):
        """Test that _onchange_index_type sets create_gin_index correctly."""
        # Create a new virtual record to test onchange in isolation
        attr = self.AttributeAttribute.new(
            {
                "name": "x_onchange_test",
                "field_description": "Test Onchange",
                "attribute_type": "integer",
                "model_id": self.test_model.id,
                "attribute_group_id": self.test_group.id,
                "serialized": True,
                "serialization_field_id": self.serialization_field.id,
                "index_type": "none",
                "create_gin_index": False,
            }
        )

        # Set index_type to gin and call onchange
        attr.index_type = "gin"
        attr._onchange_index_type()
        self.assertTrue(attr.create_gin_index)

        # Set index_type to none and call onchange
        attr.index_type = "none"
        attr._onchange_index_type()
        self.assertFalse(attr.create_gin_index)

    def test_gin_index_onchange_sets_index_type(self):
        """Test that _onchange_create_gin_index sets index_type correctly."""
        # Create a new virtual record to test onchange in isolation
        attr = self.AttributeAttribute.new(
            {
                "name": "x_gin_onchange_test",
                "field_description": "Test GIN Onchange",
                "attribute_type": "integer",
                "model_id": self.test_model.id,
                "attribute_group_id": self.test_group.id,
                "serialized": True,
                "serialization_field_id": self.serialization_field.id,
                "index_type": "none",
                "create_gin_index": False,
            }
        )

        # Set create_gin_index to True and call onchange
        attr.create_gin_index = True
        attr._onchange_create_gin_index()
        self.assertEqual(attr.index_type, "gin")

        # Set create_gin_index to False (with index_type still gin)
        attr.create_gin_index = False
        attr._onchange_create_gin_index()
        self.assertEqual(attr.index_type, "none")

    def test_btree_index_type_selection(self):
        """Test that btree is a valid index_type selection value."""
        attr = self._create_numeric_attribute(
            "btree_test", "integer", index_type="btree"
        )
        self.assertEqual(attr.index_type, "btree")

    def test_index_name_truncation(self):
        """Test that long attribute names produce valid index names."""
        # Create attribute with a very long name
        long_name = "very_long_attribute_name_that_exceeds_postgres_limits"
        attr = self._create_numeric_attribute(long_name, "integer")

        index_name = attr._get_btree_index_name()

        # PostgreSQL has a 63-character limit for identifiers
        self.assertLessEqual(len(index_name), 63)
        self.assertTrue(index_name.endswith("_btree"))
