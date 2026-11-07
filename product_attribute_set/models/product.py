# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

# When this system parameter is enabled, the native attributes of a product's
# attribute set are injected in the Attributes tab whatever action opened the
# form, not only the ones that set "include_native_attribute_view_ref".
SHOW_NATIVE_EVERYWHERE_PARAM = "product_attribute_set.show_native_attributes_everywhere"


def _show_native_attributes_everywhere(env):
    value = env["ir.config_parameter"].sudo().get_param(SHOW_NATIVE_EVERYWHERE_PARAM)
    return value not in (False, None, "", "False", "0")


class ProductTemplate(models.Model):
    _inherit = ["product.template", "attribute.set.owner.mixin"]
    _name = "product.template"

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        default=lambda self: self._get_default_att_set(),
    )

    def _get_default_att_set(self):
        """Get default product's attribute_set by category."""
        # Use the current product's category to determine default attribute set
        if self.categ_id:
            return self.categ_id.attribute_set_id.id

    @api.model_create_multi
    def create(self, vals_list):
        category_model = self.env["product.category"]
        for vals in vals_list:
            if not vals.get("attribute_set_id") and vals.get("categ_id"):
                category = category_model.browse(vals["categ_id"])
                if category.attribute_set_id:
                    vals["attribute_set_id"] = category.attribute_set_id.id
        return super().create(vals_list)

    def write(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            if category.attribute_set_id:
                vals["attribute_set_id"] = category.attribute_set_id.id
        return super().write(vals)

    @api.onchange("categ_id")
    def _onchange_categ_id(self):
        self.ensure_one()
        if self.categ_id and not self.attribute_set_id:
            self.attribute_set_id = self.categ_id.attribute_set_id

    def get_view(self, view_id=None, view_type="form", **options):
        # The product form is reached through many actions (Sales, Inventory,
        # Purchase, Accounting, MRP...) and only a couple of them set the
        # "include_native_attribute_view_ref" flag. Without it the Attributes
        # tab only injects "custom" attributes, so a product whose set is made
        # of native attributes shows an empty tab depending on the menu used.
        # When the setting is enabled, force the flag so the product's own
        # Attributes tab is populated consistently from any originating action.
        if _show_native_attributes_everywhere(self.env) and not self.env.context.get(
            "include_native_attribute_view_ref"
        ):
            self = self.with_context(include_native_attribute_view_ref=1)
        return super().get_view(view_id=view_id, view_type=view_type, **options)


class ProductProduct(models.Model):
    _inherit = ["product.product", "attribute.set.owner.mixin"]
    _name = "product.product"

    attribute_set_id = fields.Many2one(
        related="product_tmpl_id.attribute_set_id", store=True
    )

    @api.model
    def _get_attribute_set_owner_model(self):
        return [("model", "in", ("product.product", "product.template"))]

    def get_view(self, view_id=None, view_type="form", **options):
        # See ProductTemplate.get_view: ensure native attributes are injected
        # in the variant form too, whatever action opened it.
        if _show_native_attributes_everywhere(self.env) and not self.env.context.get(
            "include_native_attribute_view_ref"
        ):
            self = self.with_context(include_native_attribute_view_ref=1)
        return super().get_view(view_id=view_id, view_type=view_type, **options)
