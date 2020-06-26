# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    product_default_attribute_set_id = fields.Many2one(
        comodel_name="attribute.set",
        string="Default Product Attribute Set",
        help="Set the default attribute set that will be used as default for"
        "new products.",
    )
