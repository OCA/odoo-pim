# Copyright 2026 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Domain
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
        # Select attribute: its column is NULL when unset.
        cls.attr_material = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Range Material",
                "name": "x_range_material",
                "attribute_type": "select",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
            }
        )
        cls.material_option = cls.env["attribute.option"].create(
            {"name": "Steel", "attribute_id": cls.attr_material.id}
        )
        cls.product_no_set_with_option = ProductTemplate.create(
            {
                "name": "No Set But Has Material",
                "is_published": True,
                "website_id": cls.website.id,
                "x_range_material": cls.material_option.id,
            }
        )

        # Child set: inherits x_range_capacity from its parent.
        cls.attr_set_child = cls.env["attribute.set"].create(
            {
                "name": "Range Attribute Child Set",
                "model_id": product_model.id,
                "parent_id": cls.attr_set.id,
            }
        )
        cls.product_child_set = ProductTemplate.create(
            {
                "name": "Child Set Product",
                "is_published": True,
                "website_id": cls.website.id,
                "attribute_set_id": cls.attr_set_child.id,
                "x_range_capacity": 60,
                "x_range_material": cls.material_option.id,
            }
        )

        # Product without the attribute set: it does NOT carry the attribute,
        # but x_range_capacity is a real column defaulting to 0, so a
        # ``>= 0``/negative filter must NOT pick it up.
        cls.product_no_attr_set = ProductTemplate.create(
            {
                "name": "No Attribute Set Product",
                "is_published": True,
                "website_id": cls.website.id,
            }
        )


class TestBuildRangeFilterDomains(TransactionCase, _RangeFilterSetup):
    """Unit tests for the shared build_range_filter_domains helper."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_common()

    def test_min_and_max_returns_one_combined_sub_domain(self):
        set_ids = self.attr_capacity._get_all_set_ids()
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50, "max": 100}}
        )
        self.assertEqual(
            domains,
            [
                [
                    ("attribute_set_id", "in", set_ids),
                    ("x_range_capacity", ">=", 50),
                    ("x_range_capacity", "<=", 100),
                ],
            ],
        )
        matches = self.env["product.template"].search(domains[0])
        self.assertIn(self.product_in_range, matches)
        self.assertNotIn(self.product_below_range, matches)
        self.assertNotIn(self.product_above_range, matches)

    def test_zero_min_excludes_products_without_the_attribute(self):
        """Regression: a ``>= 0`` (or negative) bound must not match products
        that don't carry the attribute just because the column defaults to 0."""
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 0}}
        )
        matches = self.env["product.template"].search(domains[0])
        self.assertIn(self.product_in_range, matches)
        self.assertIn(self.product_below_range, matches)
        self.assertNotIn(self.product_no_attr_set, matches)

    def test_child_set_products_are_matched(self):
        """Products on a child set must survive the filter."""
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50, "max": 100}}
        )
        matches = self.env["product.template"].search(domains[0])
        self.assertIn(self.product_child_set, matches)
        self.assertIn(self.product_in_range, matches)
        self.assertNotIn(self.product_no_attr_set, matches)

    def test_only_min_or_only_max(self):
        set_ids = self.attr_capacity._get_all_set_ids()
        only_min = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50}}
        )
        self.assertEqual(
            only_min,
            [[("attribute_set_id", "in", set_ids), ("x_range_capacity", ">=", 50)]],
        )
        only_max = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"max": 100}}
        )
        self.assertEqual(
            only_max,
            [[("attribute_set_id", "in", set_ids), ("x_range_capacity", "<=", 100)]],
        )

    def test_skips_unknown_attribute(self):
        domains = build_range_filter_domains(self.env, {99999999: {"min": 0, "max": 1}})
        self.assertEqual(domains, [])

    def test_skips_empty_range(self):
        domains = build_range_filter_domains(self.env, {self.attr_capacity.id: {}})
        self.assertEqual(domains, [])


class TestSparseRangeFilterDomains(TransactionCase):
    """build_range_filter_domains on a serialized (sparse) numeric attribute.

    Sparse fields have no SQL column, so the range is resolved to a set of
    matching IDs via a raw JSONB query. The comparison is numeric, products
    without the attribute are excluded, and an empty result still filters to
    zero (it must never fall back to listing everything).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_model = cls.env.ref("product.model_product_template")
        cls.attr_group = cls.env["attribute.group"].create(
            {
                "name": "Sparse Range Group",
                "model_id": product_model.id,
                "sequence": 60,
            }
        )
        cls.attr_set = cls.env["attribute.set"].create(
            {
                "name": "Sparse Range Attribute Set",
                "model_id": product_model.id,
            }
        )
        # serialized=True makes x_sparse_capacity a sparse field backed by the
        # shared x_custom_json_attrs JSON column.
        cls.attr_capacity = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Sparse Capacity",
                "name": "x_sparse_capacity",
                "attribute_type": "integer",
                "attribute_group_id": cls.attr_group.id,
                "attribute_set_ids": [(4, cls.attr_set.id)],
                "model_id": product_model.id,
                "e_com_visibility": True,
                "e_com_filter": True,
                "e_com_range_filter": True,
                "serialized": True,
            }
        )
        ProductTemplate = cls.env["product.template"]
        cls.product_in_range = ProductTemplate.create(
            {
                "name": "Sparse In Range",
                "attribute_set_id": cls.attr_set.id,
                "x_sparse_capacity": 60,
            }
        )
        cls.product_out_range = ProductTemplate.create(
            {
                "name": "Sparse Out Range",
                "attribute_set_id": cls.attr_set.id,
                "x_sparse_capacity": 5,
            }
        )
        cls.product_no_attr_set = ProductTemplate.create(
            {"name": "Sparse No Attribute Set"}
        )
        # The range filter reads the JSON column with raw SQL, so the pending
        # values must be flushed to the database first.
        cls.env.flush_all()

    def test_field_is_sparse(self):
        field = self.env["product.template"]._fields["x_sparse_capacity"]
        self.assertTrue(getattr(field, "sparse", None))

    def test_range_resolves_to_id_in_with_numeric_comparison(self):
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 50, "max": 100}}
        )
        self.assertEqual(len(domains), 1)
        leaf = domains[0][0]
        self.assertEqual((leaf[0], leaf[1]), ("id", "in"))
        ids = leaf[2]
        self.assertIn(self.product_in_range.id, ids)
        self.assertNotIn(self.product_out_range.id, ids)
        self.assertNotIn(self.product_no_attr_set.id, ids)

    def test_zero_min_excludes_products_without_the_attribute(self):
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 0}}
        )
        ids = domains[0][0][2]
        self.assertIn(self.product_in_range.id, ids)
        self.assertIn(self.product_out_range.id, ids)
        self.assertNotIn(self.product_no_attr_set.id, ids)

    def test_empty_result_filters_to_zero(self):
        """Regression: a range that matches no product must emit ``id in []``
        (which selects nothing) instead of dropping the constraint."""
        domains = build_range_filter_domains(
            self.env, {self.attr_capacity.id: {"min": 9000}}
        )
        self.assertEqual(domains, [[("id", "in", [])]])
        self.assertFalse(self.env["product.template"].search(domains[0]))


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
        set_ids = self.attr_capacity._get_all_set_ids()
        self.assertIn(
            [
                ("attribute_set_id", "in", set_ids),
                ("x_range_capacity", ">=", 50),
                ("x_range_capacity", "<=", 100),
            ],
            base_domain,
        )

    def _value_filter_domain(self, attribute, value):
        options = self._base_options(
            additional_attribute_values=[(attribute.id, value)]
        )
        details = self.website._search_get_details(
            "products_only", "name asc, id", options
        )
        product_detail = next(
            d for d in details if d.get("model") == "product.template"
        )
        return product_detail["base_domain"]

    def test_select_filter_scope_spans_child_sets(self):
        """The scope must cover the descendant sets, not the direct ones."""
        base_domain = self._value_filter_domain(
            self.attr_material,
            f"name-attribute.option-id-{self.material_option.id}",
        )
        scope_leaf = next(
            leaf
            for domain in base_domain
            for leaf in domain
            if len(leaf) == 3 and leaf[0] == "attribute_set_id"
        )
        self.assertIn(self.attr_set.id, scope_leaf[2])
        self.assertIn(self.attr_set_child.id, scope_leaf[2])

    def test_select_filter_matches_product_on_child_set(self):
        """Products on a child set must survive the filter."""
        base_domain = self._value_filter_domain(
            self.attr_material,
            f"name-attribute.option-id-{self.material_option.id}",
        )
        matches = self.env["product.template"].search(Domain.AND(base_domain))
        self.assertIn(self.product_child_set, matches)


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

    def test_shop_zero_min_excludes_products_without_attribute(self):
        """Regression: filtering with min=0 must not list products that don't
        carry the attribute (their column defaults to 0)."""
        self.authenticate("admin", "admin")
        attr_id = self.attr_capacity.id
        url = f"/shop?additional_attr_min_{attr_id}=0"
        response = self.url_open(url, timeout=30)
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn(
            self.product_in_range.name,
            content,
            "Product carrying the attribute must appear with a min=0 filter.",
        )
        self.assertNotIn(
            self.product_no_attr_set.name,
            content,
            "Product without the attribute must NOT appear with a min=0 filter.",
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
