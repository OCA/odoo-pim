# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AttributeSetOwnerMixin(models.AbstractModel):

    _inherit = "attribute.set.owner.mixin"

    completion_rate = fields.Float(compute="_compute_completion_rate", readonly=True)
    completion_state = fields.Selection(
        selection=[("complete", "Complete"), ("not_complete", "Not complete")],
        compute="_compute_completion_rate",
        search="_search_complete_state",
    )

    @api.multi
    def _compute_completion_rate(self):
        for record in self:
            attribute_set_id = record.attribute_set_id
            completion_config = attribute_set_id.attribute_set_completeness_ids
            if completion_config:
                completion_rate = 0.0
                for criteria in completion_config:
                    field_name = criteria.field_id.name
                    if record[field_name]:
                        completion_rate += criteria.completion_rate
                record.completion_rate = completion_rate
                if completion_rate < 100:
                    record.completion_state = "not_complete"
                else:
                    record.completion_state = "complete"
            else:
                record.completion_rate = False
                record.completion_state = False

    @api.multi
    def _search_complete_state(self, operator, value):

        negative = operator in expression.NEGATIVE_TERM_OPERATORS
        default_res = expression.TRUE_DOMAIN if negative else expression.FALSE_DOMAIN

        # In case we have no value
        if not value:
            return default_res

        if operator in ["in", "not in"]:
            if len(value) > 1:
                return default_res
            value = value[0]
            operator = "!=" if negative else "="

        if operator in ["=", "!="]:
            products = self.search([("attribute_set_id", "!=", False)])
            if value not in ["complete", "not_complete"]:
                return default_res
            else:
                products = products.filtered(lambda x: x.completion_state == value)
            return [("id", "in", products.ids)]

        return default_res
