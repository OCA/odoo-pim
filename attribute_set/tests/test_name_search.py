# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import common


class TestAttributeNameSearch(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        # Do not commit
        cls.env.cr.commit = mock.Mock()
        cls.attribute = cls.env["attribute.attribute"].create(
            {
                "attribute_type": "char",
                "nature": "custom",
                "model_id": cls.model_id,
                "field_description": "Country of Origin",
                "name": "x_country_origin",
                "attribute_group_id": cls.group.id,
            }
        )

    def test_name_search_by_technical_name(self):
        """The attribute is found by its technical name."""
        results = self.env["attribute.attribute"].name_search("x_country_origin")
        self.assertIn(self.attribute.id, [r[0] for r in results])

    def test_name_search_by_field_description(self):
        """The attribute is found by its visible label (field_description)."""
        results = self.env["attribute.attribute"].name_search("Country of Origin")
        self.assertIn(self.attribute.id, [r[0] for r in results])

    def test_name_search_partial_field_description(self):
        """A partial match on the label still finds the attribute."""
        results = self.env["attribute.attribute"].name_search("Origin")
        self.assertIn(self.attribute.id, [r[0] for r in results])

    def test_name_search_negative_operator(self):
        """Negative operators exclude the matching record."""
        results = self.env["attribute.attribute"].name_search(
            "Country of Origin", operator="not ilike"
        )
        self.assertNotIn(self.attribute.id, [r[0] for r in results])

    def test_name_search_no_match(self):
        """An unrelated term does not return the attribute."""
        results = self.env["attribute.attribute"].name_search("does not exist")
        self.assertNotIn(self.attribute.id, [r[0] for r in results])
