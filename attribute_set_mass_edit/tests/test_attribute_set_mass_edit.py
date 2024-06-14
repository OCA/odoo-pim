# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAttributeSetMassEdit(TransactionCase):
    def setUp(self):
        super(TestAttributeSetMassEdit, self).setUp()
        self.model_id = self.env.ref("base.model_res_partner").id
        self.group = self.env["attribute.group"].create(
            {"name": "My Group", "model_id": self.model_id}
        )
        self.attr = self.env["attribute.attribute"].create(
            self._prepare_attr_vals("x_test")
        )
        self.attr2 = self.env["attribute.attribute"].create(
            self._prepare_attr_vals("x_test2")
        )

    def _prepare_attr_vals(self, name):
        return {
            "nature": "custom",
            "model_id": self.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": name,
            "attribute_group_id": self.group.id,
        }

    def _get_mass_object(self):
        action_server_obj = self.env["ir.actions.server"]
        return action_server_obj.search(
            [("mass_edit_attribute_group_id", "=", self.attr.attribute_group_id.id)]
        )

    def test_attr_mass_edit(self):
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.assertEqual(
            mass_object.name, f"Edit {self.attr.attribute_group_id.name} fields"
        )
        self.assertIn(
            self.attr.field_id.id, mass_object.mapped("mass_edit_line_ids.field_id").ids
        )
        self.attr.allow_mass_editing = False
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)

    def test_attr_unlink(self):
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.attr.unlink()
        self.assertFalse(mass_object.exists())

    def test_group_rename(self):
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        new_name = "New Group Name"
        self.group.name = new_name
        self.assertEqual(mass_object.name, f"Edit {new_name} fields")

    def test_group_unlink(self):
        self.attr.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.group.unlink()
        self.assertFalse(mass_object.exists())

    def test_several_attr_in_same_group(self):
        self.attr.allow_mass_editing = True
        self.attr2.allow_mass_editing = True
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.assertEqual(
            mass_object.name, f"Edit {self.attr.attribute_group_id.name} fields"
        )
        self.assertIn(
            self.attr.field_id.id, mass_object.mapped("mass_edit_line_ids.field_id").ids
        )
        self.assertIn(
            self.attr2.field_id.id,
            mass_object.mapped("mass_edit_line_ids.field_id").ids,
        )
        self.attr.allow_mass_editing = False
        mass_object = self._get_mass_object()
        self.assertTrue(mass_object)
        self.attr2.allow_mass_editing = False
        mass_object = self._get_mass_object()
        self.assertFalse(mass_object)
