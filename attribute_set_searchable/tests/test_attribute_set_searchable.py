# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock

from odoo.tests.common import SavepointCase


class TestAttributeSetSearchable(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAttributeSetSearchable, cls).setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        cls.vals = {
            "nature": "custom",
            "model_id": cls.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": "x_test_searchable",
            "attribute_group_id": cls.group.id,
        }

        cls.attr = cls.env["attribute.attribute"].create(cls.vals)
        cls.env.cr.commit = mock.Mock()

    def _get_filter(self, forced_attr=False):
        attr = forced_attr or self.attr
        filter_obj = self.env["ir.ui.custom.field.filter"]
        return filter_obj.search([("attribute_id", "=", attr.id)])

    def test_attr_searchable(self):
        custom_filter = self._get_filter()
        self.assertFalse(custom_filter)
        self.attr.searchable = True
        custom_filter = self._get_filter()
        self.assertTrue(custom_filter)
        self.assertEqual(custom_filter.model_id.id, self.model_id)
        self.assertEqual(custom_filter.name, self.attr.field_description)
        self.assertEqual(custom_filter.expression, self.attr.name)
        self.assertEqual(custom_filter.sequence, self.attr.sequence)
        self.attr.searchable = False
        custom_filter = self._get_filter()
        self.assertFalse(custom_filter)

    def test_attr_unlink(self):
        custom_filter = self._get_filter()
        self.assertFalse(custom_filter)
        self.attr.searchable = True
        custom_filter = self._get_filter()
        self.assertTrue(custom_filter)
        self.attr.with_context(_force_unlink=True).unlink()
        self.assertFalse(custom_filter.exists())

    def test_attr_create(self):
        vals = self.vals.copy()
        vals.update({"searchable": True, "name": "x_test_searchable_2"})
        attr = self.env["attribute.attribute"].create(vals)
        custom_filter = self._get_filter(forced_attr=attr)
        self.assertTrue(custom_filter)
