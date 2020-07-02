# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock

from odoo.tests.common import SavepointCase


class TestPimAttributeSetMassEdit(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPimAttributeSetMassEdit, cls).setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        vals = {
            "nature": "custom",
            "model_id": cls.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": "x_test_1",
            "attribute_group_id": cls.group.id,
            "allow_mass_editing": True,
        }

        cls.attr = cls.env["attribute.attribute"].create(vals)

    def setUp(self):
        super(TestPimAttributeSetMassEdit, self).setUp()
        commit_patcher = mock.patch.object(self.env.cr.__class__, "commit")
        commit_patcher.start()

        @self.addCleanup
        def stop_mock():
            commit_patcher.stop()

    def test_attr_mass_edit(self):
        mass_object = self.env["mass.editing"].search(
            [("attribute_group_id", "=", self.attr.attribute_group_id.id)]
        )
        pim_user_grp = self.env.ref("pim.group_pim_user")
        self.assertIn(pim_user_grp.id, mass_object.group_ids.ids)
