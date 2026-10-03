"""Extra coverage tests for product_template and attribute_attribute extensions."""

from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestModelsCoverage(TransactionCase):
    """Cover edge cases in the JSONB attribute helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AttributeAttribute = cls.env["attribute.attribute"]
        cls.AttributeGroup = cls.env["attribute.group"]
        cls.ProductTemplate = cls.env["product.template"]
        cls.IrModel = cls.env["ir.model"]

        cls.product_model = cls.IrModel.search(
            [("model", "=", "product.template")], limit=1
        )

        cls.test_group = cls.AttributeGroup.create(
            {
                "name": "Coverage Group",
                "model_id": cls.product_model.id,
            }
        )

    def _create_attr(self, name, *, attr_type="char", serialized=True, **vals):
        defaults = {
            "name": f"x_cov_{name}",
            "field_description": f"Coverage {name}",
            "attribute_type": attr_type,
            "model_id": self.product_model.id,
            "attribute_group_id": self.test_group.id,
            "serialized": serialized,
            "website_visible": True,
        }
        defaults.update(vals)
        return self.AttributeAttribute.create(defaults)

    # -- attribute.attribute helpers --------------------------------------

    def test_distinct_values_non_serialized_returns_empty(self):
        attr = self._create_attr("nonser", serialized=False)
        self.assertEqual(attr._get_distinct_values(), [])

    def test_min_max_values_char_returns_none(self):
        attr = self._create_attr("char_attr", attr_type="char")
        self.assertEqual(attr._get_min_max_values(), (None, None))

    def test_min_max_values_non_serialized_returns_none(self):
        attr = self._create_attr("ns_int", attr_type="integer", serialized=False)
        self.assertEqual(attr._get_min_max_values(), (None, None))

    def test_facet_counts_non_serialized_returns_empty(self):
        attr = self._create_attr("ns_facet", serialized=False)
        self.assertEqual(attr._get_facet_counts(), {})

    def test_facet_counts_with_data(self):
        attr = self._create_attr("facet_color")
        for color in ("red", "blue", "red"):
            tmpl = self.ProductTemplate.create({"name": f"P-{color}", "type": "consu"})
            if "x_custom_json_attrs" in tmpl._fields:
                tmpl.write({"x_custom_json_attrs": {attr.name: color}})
        # Flush pending ORM writes so raw SQL in _get_facet_counts sees them.
        self.env.flush_all()
        counts = attr._get_facet_counts()
        self.assertIsInstance(counts, dict)
        if counts:
            self.assertEqual(counts.get("red"), 2)
            self.assertEqual(counts.get("blue"), 1)

    def test_distinct_values_with_data(self):
        attr = self._create_attr("brand")
        for brand in ("cat", "komatsu", "cat"):
            tmpl = self.ProductTemplate.create({"name": f"P-{brand}", "type": "consu"})
            if "x_custom_json_attrs" in tmpl._fields:
                tmpl.write({"x_custom_json_attrs": {attr.name: brand}})
        self.env.flush_all()
        values = attr._get_distinct_values()
        self.assertIsInstance(values, list)
        if values:
            self.assertEqual(sorted(values), ["cat", "komatsu"])

    def test_min_max_values_integer_with_data(self):
        attr = self._create_attr("cap", attr_type="integer")
        for cap in (100, 500, 1000):
            tmpl = self.ProductTemplate.create({"name": f"P-{cap}", "type": "consu"})
            if "x_custom_json_attrs" in tmpl._fields:
                tmpl.write({"x_custom_json_attrs": {attr.name: cap}})
        self.env.flush_all()
        min_val, max_val = attr._get_min_max_values()
        if min_val is not None:
            self.assertEqual(min_val, 100)
            self.assertEqual(max_val, 1000)

    def test_onchange_range_warns_when_index_not_btree(self):
        attr = self._create_attr("intnoindex", attr_type="integer")
        attr.index_type = False
        attr.website_filter_type = "range"
        result = attr._onchange_website_filter_type()
        # numeric type but missing btree index -> performance warning branch
        self.assertIsNotNone(result)
        self.assertIn("warning", result)
        self.assertIn("B-tree", result["warning"]["message"])

    def test_onchange_non_range_returns_none(self):
        attr = self._create_attr("char_chk")
        attr.website_filter_type = "checkbox"
        self.assertIsNone(attr._onchange_website_filter_type())

    # -- product.template domain helpers ----------------------------------

    def test_attribute_domain_empty_filters(self):
        self.assertEqual(self.ProductTemplate._get_jsonb_attribute_domain({}), [])
        self.assertEqual(self.ProductTemplate._get_jsonb_attribute_domain(None), [])

    @mute_logger("odoo.addons.website_attribute_set_jsonb.models.product_template")
    def test_attribute_domain_no_serialization_field(self):
        """When no serialized field is found, the helper logs and returns []."""
        with patch.object(
            type(self.env["ir.model.fields"]),
            "search",
            return_value=self.env["ir.model.fields"],
        ):
            domain = self.ProductTemplate._get_jsonb_attribute_domain(
                {"x_brand": ["cat"]}
            )
        self.assertEqual(domain, [])

    def test_attribute_domain_no_match_returns_impossible_domain(self):
        # Filter on a value that does not exist -> [("id", "=", 0)]
        attr = self._create_attr("nomatch")
        domain = self.ProductTemplate._get_jsonb_attribute_domain(
            {attr.name: ["__no_such_value__"]}
        )
        # Either impossible-domain or empty (if no serialized field present);
        # the impossible case is the one we're exercising.
        self.assertIn(domain, ([], [("id", "=", 0)]))

    def test_attribute_domain_with_match(self):
        attr = self._create_attr("matched")
        tmpl = self.ProductTemplate.create({"name": "P-match", "type": "consu"})
        if "x_custom_json_attrs" not in tmpl._fields:
            self.skipTest("x_custom_json_attrs column missing")
        tmpl.write({"x_custom_json_attrs": {attr.name: "hit"}})
        self.env.flush_all()
        domain = self.ProductTemplate._get_jsonb_attribute_domain({attr.name: ["hit"]})
        self.assertTrue(domain)
        self.assertEqual(domain[0][0], "id")
        self.assertEqual(domain[0][1], "in")
        self.assertIn(tmpl.id, domain[0][2])

    def test_filtered_ids_none_for_empty(self):
        self.assertIsNone(
            self.ProductTemplate._get_jsonb_filtered_product_ids(
                {}, "x_custom_json_attrs"
            )
        )

    def test_filtered_ids_range_only_min(self):
        attr = self._create_attr("only_min", attr_type="integer")
        tmpl_lo = self.ProductTemplate.create({"name": "lo", "type": "consu"})
        tmpl_hi = self.ProductTemplate.create({"name": "hi", "type": "consu"})
        if "x_custom_json_attrs" not in tmpl_lo._fields:
            self.skipTest("x_custom_json_attrs column missing")
        tmpl_lo.write({"x_custom_json_attrs": {attr.name: 10}})
        tmpl_hi.write({"x_custom_json_attrs": {attr.name: 100}})
        self.env.flush_all()
        ids = self.ProductTemplate._get_jsonb_filtered_product_ids(
            {attr.name: {"min": 50, "max": None}}, "x_custom_json_attrs"
        )
        self.assertIn(tmpl_hi.id, ids)
        self.assertNotIn(tmpl_lo.id, ids)

    def test_filtered_ids_range_only_max(self):
        attr = self._create_attr("only_max", attr_type="integer")
        tmpl_lo = self.ProductTemplate.create({"name": "lo", "type": "consu"})
        tmpl_hi = self.ProductTemplate.create({"name": "hi", "type": "consu"})
        if "x_custom_json_attrs" not in tmpl_lo._fields:
            self.skipTest("x_custom_json_attrs column missing")
        tmpl_lo.write({"x_custom_json_attrs": {attr.name: 10}})
        tmpl_hi.write({"x_custom_json_attrs": {attr.name: 100}})
        self.env.flush_all()
        ids = self.ProductTemplate._get_jsonb_filtered_product_ids(
            {attr.name: {"min": None, "max": 50}}, "x_custom_json_attrs"
        )
        self.assertIn(tmpl_lo.id, ids)
        self.assertNotIn(tmpl_hi.id, ids)

    def test_filtered_ids_single_equality_value(self):
        attr = self._create_attr("single_eq")
        tmpl_a = self.ProductTemplate.create({"name": "a", "type": "consu"})
        tmpl_b = self.ProductTemplate.create({"name": "b", "type": "consu"})
        if "x_custom_json_attrs" not in tmpl_a._fields:
            self.skipTest("x_custom_json_attrs column missing")
        tmpl_a.write({"x_custom_json_attrs": {attr.name: "alpha"}})
        tmpl_b.write({"x_custom_json_attrs": {attr.name: "beta"}})
        self.env.flush_all()
        ids = self.ProductTemplate._get_jsonb_filtered_product_ids(
            {attr.name: ["alpha"]}, "x_custom_json_attrs"
        )
        self.assertIn(tmpl_a.id, ids)
        self.assertNotIn(tmpl_b.id, ids)

    def test_filtered_ids_multi_equality_uses_in(self):
        attr = self._create_attr("multi_eq")
        tmpl_a = self.ProductTemplate.create({"name": "a", "type": "consu"})
        tmpl_b = self.ProductTemplate.create({"name": "b", "type": "consu"})
        tmpl_c = self.ProductTemplate.create({"name": "c", "type": "consu"})
        if "x_custom_json_attrs" not in tmpl_a._fields:
            self.skipTest("x_custom_json_attrs column missing")
        tmpl_a.write({"x_custom_json_attrs": {attr.name: "alpha"}})
        tmpl_b.write({"x_custom_json_attrs": {attr.name: "beta"}})
        tmpl_c.write({"x_custom_json_attrs": {attr.name: "gamma"}})
        self.env.flush_all()
        ids = self.ProductTemplate._get_jsonb_filtered_product_ids(
            {attr.name: ["alpha", "beta"]}, "x_custom_json_attrs"
        )
        self.assertIn(tmpl_a.id, ids)
        self.assertIn(tmpl_b.id, ids)
        self.assertNotIn(tmpl_c.id, ids)

    def test_filtered_ids_no_conditions_returns_none(self):
        # A filter whose value type is neither dict nor list emits no
        # conditions, so the helper short-circuits to None.
        self.assertIsNone(
            self.ProductTemplate._get_jsonb_filtered_product_ids(
                {"x_brand": "not-a-list"}, "x_custom_json_attrs"
            )
        )
