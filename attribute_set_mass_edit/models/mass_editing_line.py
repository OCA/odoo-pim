# Copyright 2021 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MassEditingLine(models.Model):
    _inherit = "mass.editing.line"

    attribute_id = fields.Many2one(
        "attribute.attribute",
        ondelete="cascade",
    )
