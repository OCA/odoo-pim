# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AttributeSet(models.Model):
    _inherit = "attribute.set"

    attribute_set_completeness_ids = fields.One2many(
        comodel_name="attribute.set.completeness",
        inverse_name="attribute_set_id",
        string="Completeness Requirements",
        bypass_search_access=True,
    )

    @api.constrains("attribute_set_completeness_ids")
    def _check_attribute_set_completeness_ids(self):
        for attr_set in self:
            completion_config = attr_set.attribute_set_completeness_ids
            if completion_config:
                total = sum(completion_config.mapped("completion_rate"))
                if float_compare(total, 100.0, precision_digits=2):
                    raise ValidationError(
                        self.env._("Total of completion rate must be 100 %")
                    )
