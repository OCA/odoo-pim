# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AttributeGroup(models.Model):

    _inherit = "attribute.group"

    @api.multi
    def write(self, vals):
        res = super(AttributeGroup, self).write(vals)
        if "name" in vals.keys():
            for group in self:
                mass_object = self.env["mass.object"].search(
                    [("attribute_group_id", "=", group.id)]
                )
                if mass_object:
                    mass_object.name = group.name
                    mass_object.unlink_action()
                    mass_object.create_action()
        return res
