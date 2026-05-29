# Copyright 2026 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, TransactionCase, tagged

from ..models.mixins import build_range_filter_domains


class _RangeFilterSetup:
    @classmethod
    def _setup_common(cls):
        cls.website = cls.env.ref("website.default_website")
        product_model = cls.env.ref("product.model_product_template")
        cls.attr_group = cls.env["attribute.group"].create(
            {
                "name": "Range Group",
                "model_id": product_model.id,
                "sequence": 50,
            }
        )
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "Range Attribute Set",
                "model_id": product_model.id,
            }
        )

        # Non-sparse integer attribute with the range filter enabled.
        cls.attr_capacity = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Capacity Liters",
                "name": "x_range_capacity",
                "attribute_type": "integer",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_range_filter": True,
            }
        )

        ProductTemplate = cls.env["product.template"]
        cls.product_in_range = ProductTemplate.create(
            {
                "name": "In Range Product",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_range_capacity": 60,
            }
        )
        cls.product_below_range = ProductTemplate.create(
            {
                "name": "Below Range Product",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_range_capacity": 5,
            }
        )
        cls.product_above_range = ProductTemplate.create(
            {
                "name": "Above Range Product",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set.id,
                "x_range_capacity": 500,
            }
        )


class TestBuildRangeFilterDomains(TransactionCase, _RangeFilterSetup):
    """Unit tests for the shared build_range_filter_domains helper."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_common()

    def test_min_and_max_returns_two_orm_leaves(self):
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50, "max": 100}}
        )
        self.assertEqual(
            domains,
            [
                [("x_range_capacity", ">=", 50)],
                [("x_range_capacity", "<=", 100)],
            ],
        )
        matches = self.env["product.template"].search(
            [("x_range_capacity", ">=", 50), ("x_range_capacity", "<=", 100)]
        )
        self.assertIn(self.product_in_range, matches)
        self.assertNotIn(self.product_below_range, matches)
        self.assertNotIn(self.product_above_range, matches)

    def test_only_min_or_only_max(self):
        only_min = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50}}
        )
        self.assertEqual(only_min, [[("x_range_capacity", ">=", 50)]])
        only_max = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"max": 100}}
        )
        self.assertEqual(only_max, [[("x_range_capacity", "<=", 100)]])

    def test_skips_unknown_attribute(self):
        domains = build_range_filter_domains(self.env, {99999999: {"min": 0, "max": 1}})
        self.assertEqual(domains, [])

    def test_skips_empty_range(self):
        domains = build_range_filter_domains(self.env, {self.attr_capacity.id: {}})
        self.assertEqual(domains, [])


class TestSearchGetDetailsWithRangeFilter(TransactionCase, _RangeFilterSetup):
    """Ensure the website search domain includes the range filter so the main
    product listing actually filters by min/max."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_common()

    def _base_options(self, **extra):
        options = {
            "displayDescription": False,
            "displayDetail": False,
            "displayExtraDetail": False,
            "displayExtraLink": False,
            "displayImage": False,
            "allowFuzzy": False,
            "category": None,
            "tags": None,
            "min_price": 0,
            "max_price": 0,
            "attribute_value_dict": None,
            "display_currency": self.website.currency_id,
        }
        options.update(extra)
        return options

    def test_search_get_details_appends_range_domain(self):
        options = self._base_options(
            additional_range_filters={self.attr_capacity.id: {"min": 50, "max": 100}}
        )
        details = self.website._search_get_details(
            "products_only", "name asc, id", options
        )
        product_detail = next(
            d for d in details if d.get("model") == "product.template"
        )
        base_domain = product_detail["base_domain"]
        self.assertIn([("x_range_capacity", ">=", 50)], base_domain)
        self.assertIn([("x_range_capacity", "<=", 100)], base_domain)


@tagged("post_install", "-at_install")
class TestRangeFilterHttp(HttpCase, _RangeFilterSetup):
    """End-to-end check via the shop URL."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_common()

    def test_shop_range_filter_excludes_out_of_range_products(self):
        """Regression: a product whose value is outside the requested
        [min, max] range must NOT appear in the listing."""
        self.authenticate("admin", "admin")
        attr_id = self.attr_capacity.id
        url = (
            f"/shop?additional_attr_min_{attr_id}=50&additional_attr_max_{attr_id}=100"
        )
        response = self.url_open(url, timeout=30)
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn(
            self.product_in_range.name,
            content,
            "Product whose value is in the requested range must appear.",
        )
        self.assertNotIn(
            self.product_below_range.name,
            content,
            "Product whose value is below the requested range must NOT appear.",
        )
        self.assertNotIn(
            self.product_above_range.name,
            content,
            "Product whose value is above the requested range must NOT appear.",
        )

    def test_range_filter_inputs_preserve_values(self):
        """Regression: the min/max inputs must show the value the user
        submitted, not appear empty after the redirect."""
        self.authenticate("admin", "admin")
        attr_id = self.attr_capacity.id
        url = (
            f"/shop?additional_attr_min_{attr_id}=50&additional_attr_max_{attr_id}=100"
        )
        response = self.url_open(url, timeout=30)
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn(f'name="additional_attr_min_{attr_id}"', content)
        self.assertIn(f'name="additional_attr_max_{attr_id}"', content)
        self.assertRegex(
            content,
            rf'name="additional_attr_min_{attr_id}"[^>]*value="50"',
        )
        self.assertRegex(
            content,
            rf'name="additional_attr_max_{attr_id}"[^>]*value="100"',
        )
