# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeSetOwnerMixin(models.AbstractModel):

    _inherit = "attribute.set.owner.mixin"

    completion_rate = fields.Float(default=0.0, readonly=True)
    completion_state = fields.Selection(
        selection=[("complete", "Complete"), ("not_complete", "Not complete")],
        default="not_complete",
        readonly=True,
    )

    attribute_set_completeneness_ids = fields.One2many(
        related="attribute_set_id.attribute_set_completeness_ids", readonly=True,
    )
    attribute_set_not_completed_ids = fields.Many2many(
        comodel_name="attribute.set.completeness", compute="_compute_completion_rate",
    )

    def _compute_completion_rate(self):
        for record in self:
            attribute_set_id = record.attribute_set_id
            completion_config = attribute_set_id.attribute_set_completeness_ids
            if completion_config:
                completion_rate = 0.0
                not_complete_crit = self.env["attribute.set.completeness"].browse()
                for criteria in completion_config:
                    field_name = criteria.field_id.name
                    if record[field_name]:
                        completion_rate += criteria.completion_rate
                    else:
                        not_complete_crit |= criteria
                record.completion_rate = completion_rate
                record.attribute_set_not_completed_ids = not_complete_crit
                if completion_rate < 100:
                    record.completion_state = "not_complete"
                else:
                    record.completion_state = "complete"
            else:
                record.completion_rate = 0
                record.completion_state = "not_complete"
