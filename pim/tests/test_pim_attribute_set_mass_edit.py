# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestPimAttributeSetMassEdit(TransactionCase):
    def setUp(self):
        super(TestPimAttributeSetMassEdit, self).setUp()
        self.model_id = self.env.ref("base.model_res_partner").id
        self.group = self.env["attribute.group"].create(
            {"name": "My Group", "model_id": self.model_id}
        )
        vals = {
            "nature": "custom",
            "model_id": self.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": "x_test",
            "attribute_group_id": self.group.id,
            "allow_mass_editing": True,
        }

        self.attr = self.env["attribute.attribute"].create(vals)

    def test_attr_mass_edit(self):
        mass_object = self.env["mass.editing"].search(
            [("attribute_group_id", "=", self.attr.attribute_group_id.id)]
        )
        pim_user_grp = self.env.ref("pim.group_pim_user")
        self.assertIn(pim_user_grp.id, mass_object.group_ids.ids)
