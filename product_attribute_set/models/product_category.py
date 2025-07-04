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
        res = super().write(vals)
        if vals.get("attribute_set_id"):
            for category in self:
                template_ids = self.env["product.template"].search(
                    [("categ_id", "=", category.id), ("attribute_set_id", "=", False)]
                )
                template_ids.write({"attribute_set_id": category.attribute_set_id.id})
        return res
