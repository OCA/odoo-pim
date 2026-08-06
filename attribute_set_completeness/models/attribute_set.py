# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeSet(models.Model):
    _inherit = "attribute.set"

    attribute_set_completeness_ids = fields.One2many(
        comodel_name="attribute.set.completeness",
        inverse_name="attribute_set_id",
        string="Completeness Requirements",
        auto_join=True,
    )

    @api.constrains("attribute_set_completeness_ids")
    def _check_attribute_set_completeness_ids(self):
        for attr_set in self:
            completion_config = attr_set.attribute_set_completeness_ids
            if completion_config:
                total = sum([rule.completion_rate for rule in completion_config])
                if total != 100.0:
                    raise ValidationError(_("Total of completion rate must be 100 %"))
