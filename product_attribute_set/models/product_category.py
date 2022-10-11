# Copyright 2015 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Default Attribute Set",
        context={"default_model_id": "product.template"},
    )

    def write(self, vals):
        """Fill Category's products with Category's default attribute_set_id if empty"""
        super().write(vals)
        if vals.get("attribute_set_id"):
            product_ids = self.env["product.template"].search(
                [("categ_id", "=", self.id), ("attribute_set_id", "=", False)]
            )
            for product_id in product_ids:
                product_id.attribute_set_id = self.attribute_set_id

        return True
