from odoo import fields, models


class FakeProduct(models.Model):
    _inherit = "product.product"

    product_attribute = fields.Char()
