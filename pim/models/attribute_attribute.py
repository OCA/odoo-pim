# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AttributeAttribute(models.Model):

    _inherit = "attribute.attribute"

    def _prepare_create_mass_editing(self):
        data = super(AttributeAttribute, self)._prepare_create_mass_editing()
        pim_usr_grp = self.env.ref("pim.group_pim_user")
        data.update({"group_ids": [(4, pim_usr_grp.id)]})
        return data
