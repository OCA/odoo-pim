"""Tests for the WebsiteSaleJsonb controller."""

from werkzeug.datastructures import ImmutableMultiDict

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers.main import WebsiteSaleJsonb


class TestWebsiteSaleJsonbController(TransactionCase):
    """Tests covering query-param parsing in WebsiteSaleJsonb."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSaleJsonb()

    def _parse(self, args):
        with MockRequest(self.env) as req:
            req.httprequest.args = ImmutableMultiDict(args)
            return self.controller._parse_jsonb_attribute_params()

    def test_parse_empty_args(self):
        self.assertEqual(self._parse([]), {})

    def test_parse_ignores_non_jsonb_keys(self):
        self.assertEqual(
            self._parse([("search", "foo"), ("min_price", "10")]),
            {},
        )

    def test_parse_skips_empty_value(self):
        self.assertEqual(self._parse([("jsonb_x_brand", "")]), {})

    def test_parse_single_checkbox_value(self):
        self.assertEqual(
            self._parse([("jsonb_x_brand", "caterpillar")]),
            {"x_brand": ["caterpillar"]},
        )

    def test_parse_multiple_checkbox_values(self):
        self.assertEqual(
            self._parse([("jsonb_x_brand", "caterpillar,komatsu , volvo")]),
            {"x_brand": ["caterpillar", "komatsu", "volvo"]},
        )

    def test_parse_checkbox_drops_empty_tokens(self):
        # Leading/trailing commas produce empty tokens that must be filtered.
        self.assertEqual(
            self._parse([("jsonb_x_brand", ",caterpillar,,komatsu,")]),
            {"x_brand": ["caterpillar", "komatsu"]},
        )

    def test_parse_range_both_bounds(self):
        self.assertEqual(
            self._parse([("jsonb_range_x_capacity", "100-500")]),
            {"x_capacity": {"min": 100.0, "max": 500.0}},
        )

    def test_parse_range_only_min(self):
        self.assertEqual(
            self._parse([("jsonb_range_x_capacity", "100-")]),
            {"x_capacity": {"min": 100.0, "max": None}},
        )

    def test_parse_range_only_max(self):
        self.assertEqual(
            self._parse([("jsonb_range_x_capacity", "-500")]),
            {"x_capacity": {"min": None, "max": 500.0}},
        )

    @mute_logger("odoo.addons.website_attribute_set_jsonb.controllers.main")
    def test_parse_range_invalid_is_skipped(self):
        # Non-numeric range string is logged and dropped.
        self.assertEqual(
            self._parse([("jsonb_range_x_capacity", "abc-def")]),
            {},
        )

    def test_parse_range_without_hyphen_is_skipped(self):
        # Range filter without a '-' separator never matches the parser branch.
        self.assertEqual(
            self._parse([("jsonb_range_x_capacity", "100")]),
            {},
        )

    def test_parse_mixed_filters(self):
        result = self._parse(
            [
                ("jsonb_x_brand", "cat,komatsu"),
                ("jsonb_range_x_capacity", "100-500"),
                ("jsonb_x_color", "red"),
            ]
        )
        self.assertEqual(
            result,
            {
                "x_brand": ["cat", "komatsu"],
                "x_capacity": {"min": 100.0, "max": 500.0},
                "x_color": ["red"],
            },
        )

    def test_get_jsonb_attribute_values_matches_parse(self):
        # _get_jsonb_attribute_values is a thin wrapper around _parse.
        with MockRequest(self.env) as req:
            req.httprequest.args = ImmutableMultiDict([("jsonb_x_brand", "cat")])
            self.assertEqual(
                self.controller._get_jsonb_attribute_values(),
                {"x_brand": ["cat"]},
            )
