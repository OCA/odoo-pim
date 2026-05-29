# Copyright 2026 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.attribute_set.tests.test_build_view import BuildViewCase
from odoo.addons.website_attribute_set.models.mixins import search_extra


class TestSparseFieldSupport(BuildViewCase):
    """Regression tests: sparse (base_sparse_field) attributes must work with
    e-commerce search and filter without crashing.

    Background: sparse fields have field.store=False in the ORM even though
    their values are persisted in a shared JSON column. Before this fix, marking
    a sparse attribute as e_com_searchable or e_com_filter and then triggering
    a shop search/filter raised:
        ValueError: Cannot convert product.template.<field> to SQL because it
        is not stored
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_model = cls.env.ref("product.model_product_template")
        group = cls.env["attribute.group"].create(
            {
                "name": "Sparse Group",
                "model_id": product_model.id,
                "sequence": 10,
            }
        )
        attr_set = cls.env["attribute.set"].create(
            {
                "name": "Sparse Attribute Set",
                "model_id": product_model.id,
            }
        )
        # serialized=True creates the shared x_custom_json_attrs JSON column
        # and makes this field a sparse field backed by it.
        cls.attr_sparse = cls.env["attribute.attribute"].create(
            {
                "nature": "custom",
                "field_description": "Dimension",
                "name": "x_sparse_dimension",
                "attribute_type": "char",
                "attribute_group_id": group.id,
                "attribute_set_ids": [(4, attr_set.id)],
                "model_id": product_model.id,
                "serialized": True,
            }
        )
        cls.product_sparse = cls.env["product.template"].create(
            {
                "name": "Sparse Test Product",
                "type": "consu",
                "attribute_set_id": attr_set.id,
                "x_sparse_dimension": "blue_42",
            }
        )

    def test_field_is_searchable_for_sparse(self):
        self.assertTrue(self.attr_sparse.field_is_searchable)

    def test_constraint_allows_e_com_searchable_on_sparse(self):
        # Must not raise ValidationError despite field.store=False
        self.attr_sparse.write({"e_com_visibility": True, "e_com_searchable": True})

    def test_constraint_allows_e_com_filter_on_sparse(self):
        # Must not raise ValidationError despite field.store=False
        self.attr_sparse.write({"e_com_visibility": True, "e_com_filter": True})

    def test_search_extra_sparse_returns_matching_products(self):
        self.attr_sparse.write({"e_com_visibility": True, "e_com_searchable": True})
        domain = search_extra(self.env, "blue_42")
        results = self.env["product.template"].search(domain)
        self.assertIn(self.product_sparse, results)

    def test_search_with_fuzzy_sparse_no_crash(self):
        """Regression: _search_with_fuzzy must not 500 when a sparse field is
        e_com_searchable."""
        self.attr_sparse.write({"e_com_visibility": True, "e_com_searchable": True})
        self.env["website"].browse(1)._search_with_fuzzy(
            "all",
            "blue_42",
            limit=5,
            order="name asc, website_id desc, id",
            options={
                "displayDescription": False,
                "displayDetail": False,
                "displayExtraDetail": False,
                "displayExtraLink": False,
                "displayImage": False,
                "allowFuzzy": True,
            },
        )
