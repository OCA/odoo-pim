# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PimConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pim_default_product_attribute_set_id = fields.Many2one(
        related="company_id.product_default_attribute_set_id", readonly=False,
    )
