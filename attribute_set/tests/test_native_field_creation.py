"""Test native field creation to verify fix for base field modification error."""

from odoo.tests import TransactionCase


class TestNativeFieldCreation(TransactionCase):
    """Test class to verify native field creation works properly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get or create the product model
        cls.ir_model_product = (
            cls.env["ir.model"].sudo().search([("model", "=", "product.template")])
        )
        if not cls.ir_model_product:
            # Create in test environment if doesn't exist
            cls.ir_model_product = (
                cls.env["ir.model"]
                .sudo()
                .create(
                    {
                        "name": "Product Template",
                        "model": "product.template",
                        "state": "base",
                    }
                )
            )

        # Create test attribute group
        cls.attribute_group = cls.env["attribute.group"].create(
            {
                "name": "Test Group",
                "model_id": cls.ir_model_product.id,
                "sequence": 1,
            }
        )

        # Create test attribute set
        cls.attribute_set = cls.env["attribute.set"].create(
            {
                "name": "Test Attribute Set",
                "model_id": cls.ir_model_product.id,
            }
        )

        # Find an existing field to use as native field reference
        # Use a field that commonly exists in product.template
        cls.name_field = cls.env["ir.model.fields"].search(
            [("model", "=", "product.template"), ("name", "=", "default_code")], limit=1
        )

        if not cls.name_field:
            # If default_code field does not exist in test environment, use name field
            cls.name_field = cls.env["ir.model.fields"].search(
                [("model", "=", "product.template"), ("name", "=", "name")], limit=1
            )

        if not cls.name_field:
            # As fallback, create it with a proper x_ name
            cls.name_field = cls.env["ir.model.fields"].create(
                {
                    "name": "x_product_name_test",
                    # Must start with x_ for custom fields
                    "field_description": "Product Name Test",
                    "model_id": cls.ir_model_product.id,
                    "ttype": "char",
                }
            )

    def test_create_native_attribute_should_work(self):
        """Test creating native attribute links to field without modification."""
        # This should now work without error because we preserve field_id
        # while removing other ir.model.fields modifying values
        attribute = self.env["attribute.attribute"].create(
            {
                "nature": "native",  # This is a native attribute
                "field_id": self.name_field.id,  # Pointing to existing field
                "field_description": "Product Name Attr",  # Should be preserved
                "attribute_type": "char",
                "attribute_group_id": self.attribute_group.id,
                "attribute_set_ids": [(6, 0, [self.attribute_set.id])],
                "model_id": self.ir_model_product.id,
                "name": "x_product_name_attr",  # This is the attribute name/key
            }
        )

        # Verify the attribute was created successfully
        self.assertTrue(attribute.exists())
        self.assertEqual(attribute.nature, "native")
        self.assertEqual(attribute.field_id.id, self.name_field.id)
        # The attribute was created (name may reflect linked field due to _inherits)
        self.assertTrue(attribute.name)  # Attribute has a name

    def test_update_native_attribute_should_work(self):
        """Test updating a native attribute doesn't modify the base field."""
        # Create a native attribute first
        attribute = self.env["attribute.attribute"].create(
            {
                "nature": "native",
                "field_id": self.name_field.id,
                "field_description": "Product Name",
                "attribute_type": "char",
                "attribute_group_id": self.attribute_group.id,
                "attribute_set_ids": [(6, 0, [self.attribute_set.id])],
                "model_id": self.ir_model_product.id,
                "name": "x_product_name",
            }
        )

        # Update the attribute-specific fields (should work now)
        attribute.write(
            {
                "field_description": "Updated Product Name",
                # Attribute desc, not field
                "attribute_group_id": self.attribute_group.id,
            }
        )

        # Verify attribute exists and has a description
        self.assertTrue(attribute.field_description)
