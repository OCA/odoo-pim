# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeSetOwnerMixin(models.AbstractModel):

    _inherit = "attribute.set.owner.mixin"

    completion_rate = fields.Float(default=0.0, readonly=True)
    completion_state = fields.Selection(
        selection=[("complete", "Complete"), ("not_complete", "Not complete")],
        default="not_complete",
        readonly=True,
    )

    is_completion_state_visible = fields.Boolean(
        compute="_compute_is_completion_state_visible"
    )
    is_completion_rate_visible = fields.Boolean(
        compute="_compute_is_completion_rate_visible"
    )

    attribute_set_completeneness_ids = fields.One2many(
        related="attribute_set_id.attribute_set_completeness_ids", readonly=True,
    )
    attribute_set_not_completed_ids = fields.Many2many(
        comodel_name="attribute.set.completeness", compute="_compute_completion_rate",
    )

    @api.multi
    def _compute_completion_rate(self):
        for rec in self:
            attribute_set_id = rec.attribute_set_id
            completion_config = attribute_set_id.attribute_set_completeness_ids
            if completion_config:
                completion_rate = 0.0
                not_complete_crit = self.env["attribute.set.completeness"].browse()
                for criteria in completion_config:
                    field_name = criteria.field_id.name
                    if rec[field_name]:
                        completion_rate += criteria.completion_rate
                    else:
                        not_complete_crit |= criteria
                rec.completion_rate = completion_rate
                rec.attribute_set_not_completed_ids = not_complete_crit
                if completion_rate < 100:
                    rec.completion_state = "not_complete"
                else:
                    rec.completion_state = "complete"
            else:
                rec.completion_rate = 0
                rec.completion_state = "not_complete"

    @api.depends("attribute_set_id", "attribute_set_id.attribute_set_completeness_ids")
    def _compute_is_completion_state_visible(self):
        for rec in self:
            att_set_id = rec.attribute_set_id
            rec.is_completion_state_visible = (
                att_set_id and att_set_id.attribute_set_completeness_ids
            )

    @api.depends("is_completion_state_visible", "completion_state")
    def _compute_is_completion_rate_visible(self):
        for rec in self:
            rec.is_completion_rate_visible = (
                rec.is_completion_state_visible
                and rec.completion_state == "not_complete"
            )
