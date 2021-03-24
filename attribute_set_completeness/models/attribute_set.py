# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first


class AttributeSet(models.Model):

    _inherit = "attribute.set"

    attribute_set_completeness_ids = fields.One2many(
        comodel_name="attribute.set.completeness",
        inverse_name="attribute_set_id",
        string="Completeness Requirements",
        auto_join=True,
    )

    # Add a button to let the user choose between automatic completion
    # rate vs manual input
    is_automatic_rate = fields.Boolean(
        default=True, help="Equalize all the completion rates to the same percentage",
    )

    # If automatic mode, each attribut will have the same completion rate.
    # Taking account of the possible remainder depending of 100 divised
    # by the number of attributes.
    @api.onchange("is_automatic_rate")
    def _automatic_rate(self):
        for rec in self.filtered(lambda r: r.is_automatic_rate):
            if rec.is_automatic_rate:
                for attr_set in self:
                    completion_config = attr_set.attribute_set_completeness_ids
                    if completion_config:
                        list_attr = [attr.completion_rate for attr in completion_config]
                        attributs_num = len(completion_config)
                        value_attr = 100 / attributs_num
                        for attr in completion_config:
                            attr.completion_rate = int(value_attr)
                        total = sum(list_attr)
                        if total != 100:
                            remainder = 100 % attributs_num
                            first(completion_config).completion_rate += remainder

    @api.constrains("attribute_set_completeness_ids")
    def _check_attribute_set_completeness_ids(self):
        for attr_set in self:
            completion_config = attr_set.attribute_set_completeness_ids
            if completion_config:
                total = sum([rule.completion_rate for rule in completion_config])
                if total != 100.0:
                    if self.is_automatic_rate:
                        self._automatic_rate()
                    else:
                        raise ValidationError(
                            _("Total of completion rate must be 100 %")
                        )
