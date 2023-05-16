from odoo import models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["search.panel.mixin", "product.template"]
