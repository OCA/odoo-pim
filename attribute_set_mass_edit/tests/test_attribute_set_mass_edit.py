# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock

from odoo.tests.common import SavepointCase


class TestAttributeSetMassEdit(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAttributeSetMassEdit, cls).setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        vals = {
            "nature": "custom",
            "model_id": cls.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": "x_test_mass",
            "attribute_group_id": cls.group.id,
        }

        cls.attr = cls.env["attribute.attribute"].create(vals)

    def setUp(self):
        super(TestAttributeSetMassEdit, self).setUp()
        commit_patcher = mock.patch.object(self.env.cr.__class__, "commit")
        commit_patcher.start()

        @self.addCleanup
        def stop_mock():
            commit_patcher.stop()

    def _get_mass_object(self):
        mass_obj = self.env["mass.object"]
        return mass_obj.search(
            [("attribute_group_id", "=", self.attr.attribute_group_id.id)]
        )

    def test_attr_mass_edit(self):
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.assertEqual(mass_object.name, self.attr.attribute_group_id.name)
        self.assertIn(self.attr.field_id.id, mass_object.field_ids.ids)
        self.attr.allow_mass_editing = False
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)

    def test_attr_unlink(self):
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.attr.with_context(_force_unlink=True).unlink()
        self.assertFalse(mass_object.exists())

    def test_group_rename(self):
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        new_name = "New Group Name"
        self.group.name = new_name
        self.assertEqual(mass_object.name, new_name)
        action_name = "Mass Editing (%s)" % new_name
        self.assertEqual(mass_object.ref_ir_act_window_id.name, action_name)

    def test_group_unlink(self):
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.group.unlink()
        self.assertFalse(mass_object.exists())
