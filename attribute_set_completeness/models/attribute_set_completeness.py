# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeSetCompleteness(models.Model):

    _name = "attribute.set.completeness"
    _description = "Attribute Set Completeness"

    attribute_set_id = fields.Many2one(
        "attribute.set", required=True, ondelete="cascade"
    )
    field_id = fields.Many2one(
        "ir.model.fields", "Field Name", required=True, ondelete="cascade"
    )
    field_description = fields.Char(
        related="field_id.field_description", string="Field Description", store=True
    )
    completion_rate = fields.Float()
    model_id = fields.Many2one(related="attribute_set_id.model_id")
