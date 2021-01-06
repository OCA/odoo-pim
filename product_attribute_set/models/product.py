# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ProductTemplate(models.Model):
    """The mixin 'attribute.set.owner.mixin' override the model's fields_view_get()
    method which will replace the 'attributes_placeholder' by a group made up of all
    the product.template's Attributes.
    Each Attribute will have a conditional invisibility depending on its Attriute Sets.
    """

    _inherit = ["product.template", "attribute.set.owner.mixin"]
    _name = "product.template"

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        default=lambda self: self._get_default_att_set(),
    )

    def _get_default_att_set(self):
        """Fill default Product's attribute_set with its Category's
        default attribute_set."""
        default_categ_id_id = self._get_default_category_id()
        if default_categ_id_id:
            default_categ_id = self.env["product.category"].search(
                [("id", "=", default_categ_id_id.id)]
            )
            return default_categ_id.attribute_set_id.id

    @api.model
    def create(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            vals["attribute_set_id"] = category.attribute_set_id.id
        return super().create(vals)

    def write(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            vals["attribute_set_id"] = category.attribute_set_id.id
        return super().write(vals)

    @api.onchange("categ_id")
    def update_att_set_onchange_categ_id(self):
        self.ensure_one()
        if self.categ_id and not self.attribute_set_id:
            self.attribute_set_id = self.categ_id.attribute_set_id


# TODO : add the 'attribute.set.owner.mixin' to product.product in order to display
# Attributes in Variants.
