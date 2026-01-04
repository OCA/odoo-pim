"""Tests for B-tree expression indexes on serialized attributes."""

from odoo.tests.common import TransactionCase


class TestBtreeExpressionIndexes(TransactionCase):
    """Test cases for B-tree expression indexes on serialized attributes."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()
        cls.AttributeAttribute = cls.env["attribute.attribute"]
        cls.AttributeGroup = cls.env["attribute.group"]

        # Use res.partner model for testing
        cls.test_model = cls.env.ref("base.model_res_partner")

        # Create an attribute group for testing
        cls.test_group = cls.AttributeGroup.create(
            {
                "name": "Test JSONB B-tree Group",
                "model_id": cls.test_model.id,
            }
        )

    def _create_numeric_attribute(self, name, attr_type="integer", index_type="none"):
        """Helper to create a serialized numeric test attribute."""
        return self.AttributeAttribute.create(
            {
                "name": f"x_{name}",
                "field_description": f"Test {name.title()}",
                "attribute_type": attr_type,
                "model_id": self.test_model.id,
                "attribute_group_id": self.test_group.id,
                "serialized": True,
                "index_type": index_type,
            }
        )

    def _check_btree_index_exists(self, attribute):
        """Check if the B-tree expression index exists for an attribute."""
        index_name = attribute._get_btree_index_name()
        if not index_name:
            return False

        table_name = attribute._get_table_name()
        self.env.cr.execute(
            """
            SELECT 1 FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            """,
            (table_name, index_name),
        )
        return bool(self.env.cr.fetchone())

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

    def test_can_create_btree_index(self):
        """Test _can_create_btree_index method."""
        int_attr = self._create_numeric_attribute("int_attr", "integer")
        float_attr = self._create_numeric_attribute("float_attr", "float")
        date_attr = self._create_numeric_attribute("date_attr", "date")
        char_attr = self._create_numeric_attribute("char_attr", "char")

        self.assertTrue(int_attr._can_create_btree_index())
        self.assertTrue(float_attr._can_create_btree_index())
        self.assertTrue(date_attr._can_create_btree_index())
        self.assertFalse(char_attr._can_create_btree_index())

    def test_create_btree_index_integer(self):
        """Test B-tree index creation for integer attributes."""
        attr = self._create_numeric_attribute(
            "btree_int", "integer", index_type="btree"
        )

        self.assertEqual(attr.index_type, "btree")
        self.assertTrue(
            self._check_btree_index_exists(attr),
            "B-tree index should exist after attribute creation",
        )

    def test_create_btree_index_float(self):
        """Test B-tree index creation for float attributes."""
        attr = self._create_numeric_attribute(
            "btree_float", "float", index_type="btree"
        )

        self.assertEqual(attr.index_type, "btree")
        self.assertTrue(
            self._check_btree_index_exists(attr),
            "B-tree index should exist for float attribute",
        )

    def test_btree_index_fails_for_char(self):
        """Test that B-tree index is not created for char attributes."""
        attr = self._create_numeric_attribute("btree_char", "char", index_type="btree")

        self.assertEqual(attr.index_type, "btree")
        self.assertFalse(
            self._check_btree_index_exists(attr),
            "B-tree index should not be created for char attribute",
        )

    def test_disable_btree_index(self):
        """Test disabling B-tree index by setting index_type to none."""
        attr = self._create_numeric_attribute(
            "disable_btree", "integer", index_type="btree"
        )

        # Initially B-tree index exists
        self.assertTrue(self._check_btree_index_exists(attr))

        # Disable index
        attr.write({"index_type": "none"})

        # Index should be gone
        self.assertFalse(self._check_btree_index_exists(attr))

    def test_delete_btree_indexed_attribute(self):
        """Test that B-tree index is dropped when attribute is deleted."""
        attr = self._create_numeric_attribute(
            "delete_btree", "integer", index_type="btree"
        )

        index_name = attr._get_btree_index_name()
        table_name = attr._get_table_name()

        # Initially index exists
        self.assertTrue(self._check_btree_index_exists(attr))

        # Delete attribute
        attr.unlink()

        # Check index is gone
        self.env.cr.execute(
            """
            SELECT 1 FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            """,
            (table_name, index_name),
        )
        self.assertFalse(
            self.env.cr.fetchone(),
            "B-tree index should be dropped after attribute deletion",
        )

    def test_index_type_onchange_sync(self):
        """Test that index_type and create_gin_index stay in sync."""
        attr = self._create_numeric_attribute("sync_test", "integer")

        # Set index_type to gin
        attr.index_type = "gin"
        attr._onchange_index_type()
        self.assertTrue(attr.create_gin_index)

        # Set index_type to none
        attr.index_type = "none"
        attr._onchange_index_type()
        self.assertFalse(attr.create_gin_index)

        # Set create_gin_index directly
        attr.create_gin_index = True
        attr._onchange_create_gin_index()
        self.assertEqual(attr.index_type, "gin")
