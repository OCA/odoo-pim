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
    field_description = fields.Char(related="field_id.field_description")
    completion_rate = fields.Float()
    completion_rate_progress = fields.Float(
        string="Completion Rate Progress", related="completion_rate"
    )
    model_id = fields.Many2one(related="attribute_set_id.model_id")

    @api.depends(
        "attribute_set_id.complete_attribute_ids",
        "attribute_set_id.attribute_set_completeness_ids.field_id",
    )
    def _compute_available_field_ids(self):
        for rec in self:
            attr_set = rec.attribute_set_id
            att_set_field_ids = attr_set.complete_attribute_ids.field_id
            chosen_field_ids = attr_set.attribute_set_completeness_ids.field_id
            rec.available_field_ids = att_set_field_ids - chosen_field_ids

    @api.depends("field_id.field_description")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.field_id.field_description or ""
