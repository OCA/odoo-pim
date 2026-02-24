from odoo import fields, models


class FakeProduct(models.Model):
    _inherit = "product.product"  # pylint: disable=consider-merging-classes-inherited

    product_attribute = fields.Char()
