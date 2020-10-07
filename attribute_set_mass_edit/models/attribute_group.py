# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.fields import first


class AttributeGroup(models.Model):

    _inherit = "attribute.group"

    @api.multi
    def write(self, vals):
        res = super(AttributeGroup, self).write(vals)
        if "name" in vals.keys():
            mass_editings = self.env["mass.editing"].search(
                [("attribute_group_id", "in", self.ids)]
            )
            for group in self:
                mass_editing = first(
                    mass_editings.filtered(lambda o: o.attribute_group_id == group)
                )
                if mass_editing:
                    mass_editing.name = group.name
                    # TODO: we should use tests.Form IMO
                    mass_editing.action_name = mass_editing._prepare_action_name()
                    mass_editing.disable_mass_operation()
                    mass_editing.enable_mass_operation()
        return res
