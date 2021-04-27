# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeSetCompleteness(models.Model):
    _name = "attribute.set.completeness"
    _description = "Attribute Set Completeness"
    _rec_name = "field_id"

    attribute_set_id = fields.Many2one(
        "attribute.set", required=True, ondelete="cascade"
    )
    available_field_ids = fields.Many2many(
        string="Attribute Set's fields",
        comodel_name="ir.model.fields",
        compute="_compute_available_field_ids",
        help="Fields related to the Attribute set's attributes",
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
    completion_rate_progress = fields.Float(
        string="Completion Rate Progress", related="completion_rate", readonly=True
    )
    model_id = fields.Many2one(related="attribute_set_id.model_id", readonly=True)

    @api.depends("attribute_set_id")
    def _compute_available_field_ids(self):
        for rec in self:
            att_set_field_ids = rec.attribute_set_id.attribute_ids.mapped("field_id")
            att_set_complete_ids = rec.attribute_set_id.attribute_set_completeness_ids
            choosen_field_ids = att_set_complete_ids.mapped("field_id")
            rec.available_field_ids = att_set_field_ids - choosen_field_ids

    def name_get(self):
        return [(rec.id, rec.field_id.field_description) for rec in self]
