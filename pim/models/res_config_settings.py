# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PimConfigSettings(models.TransientModel):
    _name = "pim.config.settings"
    _inherit = "res.config.settings"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    pim_default_product_attribute_set_id = fields.Many2one(
        comodel_name="attribute.set",
        related="company_id.product_default_attribute_set_id",
        readonly=False,
    )
