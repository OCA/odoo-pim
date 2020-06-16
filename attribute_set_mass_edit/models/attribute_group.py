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
            mass_objects = self.env["mass.object"].search(
                [("attribute_group_id", "in", self.ids)]
            )
            for group in self:
                mass_object = first(
                    mass_objects.filtered(lambda o: o.attribute_group_id == group)
                )
                if mass_object:
                    mass_object.name = group.name
                    mass_object.unlink_action()
                    mass_object.create_action()
        return res
