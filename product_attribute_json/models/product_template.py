from odoo import models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["pim.mixin", "product.template"]
