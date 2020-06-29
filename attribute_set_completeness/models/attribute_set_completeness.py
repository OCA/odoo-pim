# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeSetCompleteness(models.Model):

    _name = "attribute.set.completeness"
    _description = "Attribute Set Completeness"
    _rec_name = "field_id"

    attribute_set_id = fields.Many2one(
        "attribute.set", required=True, ondelete="cascade"
    )
    field_id = fields.Many2one(
        "ir.model.fields", "Field Name", required=True, ondelete="cascade"
    )
    field_description = fields.Char(
        related="field_id.field_description",
        string="Field Description",
        store=True,
        readonly=True,
    )
    completion_rate = fields.Float()
    completion_rate_progress = fields.Float(related="completion_rate", readonly=True)
    model_id = fields.Many2one(related="attribute_set_id.model_id", readonly=True)
