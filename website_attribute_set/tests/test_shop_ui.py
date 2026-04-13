"""UI-level tests for the website_attribute_set shop features.

These tests verify that the e_com_filter / e_com_specification fields actually
control what appears in the rendered HTML: filter panel and product page
specifications table.
"""

from lxml import etree

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestShopFilterUI(HttpCase):
    """Verify that additional attribute filters render correctly in the shop."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.product_model = cls.env.ref("product.model_product_template")

        cls.attr_group = cls.env["attribute.group"].create(
            {
                "name": "UI Test Group",
                "model_id": cls.product_model.id,
                "sequence": 1,
            }
        )
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "UI Test Attribute Set",
                "model_id": cls.product_model.id,
            }
        )

        # Attribute visible as filter AND specification
        cls.attr_color = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Test Color",
                "name": "x_uitest_color",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_specification": True,
            }
        )

        # Attribute visible as specification only (NOT as filter)
        cls.attr_weight = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Test Weight",
                "name": "x_uitest_weight",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": False,
                "e_com_specification": True,
            }
        )

        # Attribute visible as filter only (NOT as specification)
        cls.attr_origin = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Test Origin",
                "name": "x_uitest_origin",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_specification": False,
            }
        )

        # Boolean attribute as filter
        cls.attr_available = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Test Available",
                "name": "x_uitest_available",
                "attribute_type": "boolean",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_specification": True,
            }
        )

        # Create products
        cls.product_a = cls.env["product.template"].create(
            {
                "name": "UI Test Product Alpha",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_uitest_color": "Red",
                "x_uitest_weight": "1.5 kg",
                "x_uitest_origin": "Spain",
                "x_uitest_available": True,
            }
        )
        cls.product_b = cls.env["product.template"].create(
            {
                "name": "UI Test Product Beta",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_uitest_color": "Blue",
                "x_uitest_weight": "2.0 kg",
                "x_uitest_origin": "France",
                "x_uitest_available": False,
            }
        )

    def _get_html(self, url):
        """Fetch a page and return parsed HTML tree."""
        self.authenticate("admin", "admin")
        response = self.url_open(url, timeout=30)
        self.assertEqual(response.status_code, 200)
        return etree.fromstring(response.content, etree.HTMLParser())

    def _get_filter_headings(self, tree):
        """Extract additional attribute filter heading texts from the shop page."""
        # Desktop: id="o_products_additional_attributes_{id}", heading replaced by
        #          div.accordion-header.h6 > button > b
        # Mobile:  id="o_wsale_offcanvas_additional_attribute_{id}", heading
        #          in h2 > button > b
        headings = tree.xpath(
            "//div[starts-with(@id, 'o_products_additional_attributes_')"
            " or starts-with(@id, 'o_wsale_offcanvas_additional_attribute_')]"
            "/preceding-sibling::*//b"
        )
        return [
            etree.tostring(h, encoding="unicode", method="text").strip()
            for h in headings
        ]

    def _get_product_names(self, tree):
        """Extract product names from the shop product grid."""
        name_texts = tree.xpath("//div[contains(@class, 'oe_product')]//h6//text()")
        return [n.strip() for n in name_texts if n.strip()]

    # ── Shop filter panel tests ──

    def test_filter_attribute_appears_in_shop(self):
        """Attributes with e_com_filter=True must appear in the shop filter panel."""
        tree = self._get_html("/shop")
        filter_headings = self._get_filter_headings(tree)
        self.assertIn(
            "UI Test Color",
            filter_headings,
            "Attribute with e_com_filter=True should appear in the shop filter panel",
        )
        self.assertIn(
            "UI Test Origin",
            filter_headings,
            "Attribute with e_com_filter=True should appear in the shop filter panel",
        )

    def test_non_filter_attribute_hidden_in_shop(self):
        """Attributes with e_com_filter=False must NOT appear in the filter panel."""
        tree = self._get_html("/shop")
        filter_headings = self._get_filter_headings(tree)
        self.assertNotIn(
            "UI Test Weight",
            filter_headings,
            "Attribute with e_com_filter=False should NOT appear in the filter panel",
        )

    def test_boolean_filter_renders_checkboxes(self):
        """Boolean attributes should render as checkboxes with Yes/No labels."""
        tree = self._get_html("/shop")
        boolean_inputs = tree.xpath(
            f"//input[@name='additional_attribute_values']"
            f"[contains(@value, '{self.attr_available.id}-')]"
        )
        self.assertTrue(
            boolean_inputs,
            "Boolean filter attribute should render checkbox inputs",
        )

    def test_char_filter_renders_select(self):
        """Char attributes should render as a <select> dropdown."""
        tree = self._get_html("/shop")
        selects = tree.xpath(
            f"//div[@id='o_products_additional_attributes_{self.attr_color.id}']"
            f"//select[@name='additional_attribute_values']"
        )
        self.assertTrue(
            selects,
            "Char filter attribute should render as a <select> dropdown",
        )
        # Check that the values appear as options
        options = selects[0].xpath(".//option[text()]")
        option_texts = [
            etree.tostring(opt, encoding="unicode", method="text").strip()
            for opt in options
        ]
        self.assertIn("Red", option_texts)
        self.assertIn("Blue", option_texts)

    # ── Filter application tests ──

    def test_boolean_filter_filters_products(self):
        """Applying a boolean filter should hide non-matching products."""
        self.authenticate("admin", "admin")
        attr_id = self.attr_available.id
        response = self.url_open(
            f"/shop?additional_attribute_values={attr_id}-True", timeout=30
        )
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn("UI Test Product Alpha", content)
        self.assertNotIn(
            "UI Test Product Beta",
            content,
            "Product with x_uitest_available=False should be filtered out",
        )

    def test_char_filter_filters_products(self):
        """Applying a char filter should show only matching products."""
        self.authenticate("admin", "admin")
        attr_id = self.attr_color.id
        response = self.url_open(
            f"/shop?additional_attribute_values={attr_id}-Red", timeout=30
        )
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn("UI Test Product Alpha", content)
        self.assertNotIn(
            "UI Test Product Beta",
            content,
            "Product with x_uitest_color=Blue should be filtered out "
            "when filtering by Red",
        )


@tagged("post_install", "-at_install")
class TestProductPageUI(HttpCase):
    """Verify that specifications render correctly on the product page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.product_model = cls.env.ref("product.model_product_template")

        cls.attr_group = cls.env["attribute.group"].create(
            {
                "name": "UI Spec Test Group",
                "model_id": cls.product_model.id,
                "sequence": 1,
            }
        )
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "UI Spec Test Attribute Set",
                "model_id": cls.product_model.id,
            }
        )

        # Specification-visible attribute
        cls.attr_material = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Spec Material",
                "name": "x_uispec_material",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": False,
                "e_com_specification": True,
            }
        )

        # Filter-only attribute (should NOT appear in specifications)
        cls.attr_sku = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "UI Spec SKU Code",
                "name": "x_uispec_sku",
                "attribute_type": "char",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": cls.product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_specification": False,
            }
        )

        cls.product = cls.env["product.template"].create(
            {
                "name": "UI Spec Test Product",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_uispec_material": "Stainless Steel",
                "x_uispec_sku": "SKU-12345",
            }
        )

    def _get_html(self, url):
        self.authenticate("admin", "admin")
        response = self.url_open(url, timeout=30)
        self.assertEqual(response.status_code, 200)
        return etree.fromstring(response.content, etree.HTMLParser())

    def test_specification_attribute_appears_on_product_page(self):
        """Attributes with e_com_specification=True should appear in the
        specifications table on the product page."""
        tree = self._get_html(f"/shop/{self.product.id}")
        spec_items = tree.xpath("//li[contains(@class, 'variant_attribute')]")
        self.assertTrue(
            spec_items,
            "Specifications section should be present on the product page",
        )
        spec_text = "".join(
            etree.tostring(li, encoding="unicode", method="text") for li in spec_items
        )
        self.assertIn(
            "Stainless Steel",
            spec_text,
            "Specification attribute value should appear on the product page",
        )
        self.assertIn(
            "UI Spec Material",
            spec_text,
            "Specification attribute label should appear on the product page",
        )

    def test_non_specification_attribute_hidden_on_product_page(self):
        """Attributes with e_com_specification=False should NOT appear
        in the specifications table."""
        tree = self._get_html(f"/shop/{self.product.id}")
        spec_items = tree.xpath("//li[contains(@class, 'variant_attribute')]")
        if spec_items:
            spec_text = "".join(
                etree.tostring(li, encoding="unicode", method="text")
                for li in spec_items
            )
            self.assertNotIn(
                "SKU-12345",
                spec_text,
                "Attribute with e_com_specification=False should NOT appear "
                "in the specifications table",
            )
            self.assertNotIn(
                "UI Spec SKU Code",
                spec_text,
                "Attribute label with e_com_specification=False should NOT appear "
                "in the specifications table",
            )

    def test_product_without_attributes_has_no_spec_section(self):
        """Products without attribute sets should not show a specs section."""
        product = self.env["product.template"].create(
            {
                "name": "Plain Product No Specs",
                "is_published": True,
                "website_id": self.website.id,
            }
        )
        tree = self._get_html(f"/shop/{product.id}")
        spec_items = tree.xpath("//li[contains(@class, 'variant_attribute')]")
        self.assertFalse(
            spec_items,
            "Product without attribute set should not have a specifications section",
        )
