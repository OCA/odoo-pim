# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrUiCustomFieldFilter(models.Model):

    _inherit = "ir.ui.custom.field.filter"

    attribute_id = fields.Many2one("attribute.attribute", ondelete="cascade")
