# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeGroup(models.Model):
    _inherit = "attribute.group"

    mass_edit_action_ids = fields.One2many(
        "ir.actions.server", inverse_name="mass_edit_attribute_group_id"
    )

    def write(self, vals):
        res = super(AttributeGroup, self).write(vals)
        if "name" in vals.keys():
            mass_editings = self.env["ir.actions.server"].search(
                [("mass_edit_attribute_group_id", "in", self.ids)]
            )
            for group in self:
                mass_editing = fields.first(
                    mass_editings.filtered(
                        lambda o: o.mass_edit_attribute_group_id == group
                    )
                )
                if mass_editing:
                    mass_editing.name = group.name
                    # mass_editing.disable_mass_operation()
                    # mass_editing.enable_mass_operation()
        return res
