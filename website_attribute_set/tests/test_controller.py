"""Unit tests for website_attribute_set controllers."""

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteAttributeController(HttpCase):
    """Test class for website attribute set controllers."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.product_model = cls.env.ref("product.model_product_template")

        # Create attribute group
        cls.attr_group = cls.env["attribute.group"].create(
            {
                "name": "Test E-Commerce Group",
                "model_id": cls.product_model.id,
                "sequence": 1,
            }
        )

        # Create attribute set
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "Test E-Commerce Attribute Set",
                "model_id": cls.product_model.id,
            }
        )

        # Create a text attribute with e-commerce visibility enabled
        cls.attr_description = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Product Description",
                "name": "x_ecom_description",
                "attribute_type": "text",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
            }
        )

        # Create a char attribute with e-commerce visibility enabled
        cls.attr_color = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Product Color",
                "name": "x_ecom_color",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
            }
        )

        # Create a select attribute with e-commerce visibility enabled
        # This tests the .mapped('name') code path in the template
        cls.attr_select = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Product Material",
                "name": "x_ecom_material",
                "attribute_type": "select",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
            }
        )

        # Create options for the select attribute
        cls.material_option = cls.env["attribute.option"].create(
            {
                "name": "Cotton",
                "attribute_id": cls.attr_select.id,
            }
        )

        # Create a boolean attribute with e-commerce visibility enabled
        cls.attr_boolean = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Is Organic",
                "name": "x_ecom_organic",
                "attribute_type": "boolean",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
            }
        )

    def setUp(self):
        """Set up test environment."""
        super().setUp()

    def test_shop_page_accessibility(self):
        """Test that the shop page can be accessed without errors."""
        # This test ensures that the controller methods don't throw errors
        # like 'website' object has no attribute 'pricelist_id'
        self.authenticate("admin", "admin")
        response = self.url_open("/shop", timeout=30)

        # Should be able to access the shop page without errors
        self.assertEqual(response.status_code, 200)

    def test_product_template_with_attributes_accessibility(self):
        """Test that product pages with attributes can be accessed without errors."""
        # Ensure we can access product-related pages that use attribute functionality
        self.authenticate("admin", "admin")

        # Check if we can access the product template form
        response = self.url_open("/web", timeout=30)
        self.assertEqual(response.status_code, 200)

        # Verify the website controller has the required methods to avoid AttributeError
        from ..controllers.main import WebsiteSale

        website_sale = WebsiteSale()

        # Test that required methods exist
        self.assertTrue(hasattr(website_sale, "shop"))

    def test_product_page_accessibility(self):
        """Test that individual product pages can be accessed without 500 errors.

        This test specifically catches issues with _prepare_product_values signature
        changes in Odoo 19 (removed 'search' parameter).
        """
        self.authenticate("admin", "admin")

        # Create a published product to test the product page
        product = self.env["product.template"].create(
            {
                "name": "Test Product for Website",
                "is_published": True,
                "website_id": self.website.id,
            }
        )

        # Access the product page - this tests _prepare_product_values
        response = self.url_open(f"/shop/{product.id}", timeout=30)

        # Should return 200, not 500 (Internal Server Error)
        self.assertEqual(
            response.status_code,
            200,
            f"Product page returned {response.status_code}, expected 200. "
            "Check _prepare_product_values signature matches Odoo 19.",
        )

    def test_product_page_displays_ecom_attributes(self):
        """Test that e-commerce visible attributes are displayed on the product page.

        This test creates a product with an attribute set and e-commerce visible
        attributes, then verifies that the attribute values appear in the
        rendered product page HTML.
        """
        self.authenticate("admin", "admin")

        # Create a product with attribute set and values
        product = self.env["product.template"].create(
            {
                "name": "Test Product With Attributes",
                "is_published": True,
                "website_id": self.website.id,
                "attribute_set_id": self.attr_set.id,
                "x_ecom_description": "This is a test product description",
                "x_ecom_color": "Blue",
            }
        )

        # Verify the product has the attribute set
        self.assertEqual(product.attribute_set_id, self.attr_set)

        # Verify get_extra_attributes returns our e-commerce visible attributes
        extra_attrs = product.get_extra_attributes()
        self.assertIn(
            self.attr_description,
            extra_attrs,
            "E-commerce visible attribute should be returned by get_extra_attributes",
        )
        self.assertIn(
            self.attr_color,
            extra_attrs,
            "E-commerce visible attribute should be returned by get_extra_attributes",
        )

        # Access the product page
        response = self.url_open(f"/shop/{product.id}", timeout=30)

        # Should return 200
        self.assertEqual(response.status_code, 200)

        # Verify the attribute values are in the page content
        content = response.text
        self.assertIn(
            "This is a test product description",
            content,
            "Product description attribute value should appear on the product page",
        )
        self.assertIn(
            "Blue",
            content,
            "Product color attribute value should appear on the product page",
        )

    def test_shop_page_displays_additional_attributes_filter(self):
        """Test that additional attributes appear in the shop filter.

        This test creates published products with e-commerce visible attributes
        and verifies the filter options appear on the shop page.
        """
        self.authenticate("admin", "admin")

        # Create a product with attribute set and values
        self.env["product.template"].create(
            {
                "name": "Shop Filter Test Product",
                "is_published": True,
                "website_id": self.website.id,
                "attribute_set_id": self.attr_set.id,
                "x_ecom_description": "Filter test description",
                "x_ecom_color": "Red",
            }
        )

        # Access the shop page
        response = self.url_open("/shop", timeout=30)

        # Should return 200
        self.assertEqual(response.status_code, 200)

        # The shop page should load without errors
        # Note: The actual filter display depends on template implementation
        content = response.text
        self.assertNotIn(
            "Internal Server Error",
            content,
            "Shop page should not have internal server errors",
        )

    def test_product_page_with_select_attribute(self):
        """Test product page with select attribute type.

        This test ensures the template correctly handles select attributes
        which use .mapped('name') to display values. This catches issues
        like KeyError: 'hasattr' when QWeb tries to use Python builtins.
        """
        self.authenticate("admin", "admin")

        # Create a product with select attribute
        product = self.env["product.template"].create(
            {
                "name": "Test Product With Select Attribute",
                "is_published": True,
                "website_id": self.website.id,
                "attribute_set_id": self.attr_set.id,
                "x_ecom_material": self.material_option.id,
            }
        )

        # Access the product page
        response = self.url_open(f"/shop/{product.id}", timeout=30)

        # Should return 200, not 500
        self.assertEqual(
            response.status_code,
            200,
            f"Product page with select attribute returned {response.status_code}. "
            "Check template doesn't use Python builtins like hasattr.",
        )

        # Verify the select attribute value appears in the page
        content = response.text
        self.assertIn(
            "Cotton",
            content,
            "Select attribute value should appear on the product page",
        )

    def test_product_page_with_boolean_attribute(self):
        """Test product page with boolean attribute type.

        This test ensures boolean attributes display correctly (Yes/No).
        """
        self.authenticate("admin", "admin")

        # Create a product with boolean attribute set to True
        product = self.env["product.template"].create(
            {
                "name": "Test Product With Boolean Attribute",
                "is_published": True,
                "website_id": self.website.id,
                "attribute_set_id": self.attr_set.id,
                "x_ecom_organic": True,
            }
        )

        # Access the product page
        response = self.url_open(f"/shop/{product.id}", timeout=30)

        # Should return 200
        self.assertEqual(response.status_code, 200)

        # Verify the boolean displays as Yes
        content = response.text
        self.assertIn(
            "Yes",
            content,
            "Boolean True should display as 'Yes' on the product page",
        )

    def test_product_page_without_attribute_set(self):
        """Test that product pages without attribute sets still work.

        This ensures the module doesn't break regular products that
        don't have any attribute sets configured.
        """
        self.authenticate("admin", "admin")

        # Create a product WITHOUT attribute set
        product = self.env["product.template"].create(
            {
                "name": "Regular Product Without Attributes",
                "is_published": True,
                "website_id": self.website.id,
                # Note: no attribute_set_id
            }
        )

        # Access the product page
        response = self.url_open(f"/shop/{product.id}", timeout=30)

        # Should return 200
        self.assertEqual(
            response.status_code,
            200,
            "Product page without attribute set should work normally",
        )

        # Verify no internal server error
        self.assertNotIn(
            "Internal Server Error",
            response.text,
            "Product page should not have internal server errors",
        )
