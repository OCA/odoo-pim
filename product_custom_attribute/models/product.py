# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from lxml import etree
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.model
    def create(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            vals["attribute_set_id"] = category.attribute_set_id.id
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        if not vals.get("attribute_set_id") and vals.get("categ_id"):
            category = self.env["product.category"].browse(vals["categ_id"])
            vals["attribute_set_id"] = category.attribute_set_id.id
        super(ProductTemplate, self).write(vals)
        return True

    @api.multi
    def save_and_close_product_attributes(self):
        return True

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super(ProductTemplate, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form":
            # Create the product's attributes notebook
            att_obj = self.env['attribute.attribute']
            attribute_ids = att_obj.with_context(product_custom_attribute=True).search([
                ('attribute_set_ids', '!=', False),
                ('model_id', '=', "product.template"),
            ])
            notebook = att_obj.with_context(product_custom_attribute=True)\
                ._build_attributes_notebook(attribute_ids)
            # Add it to the product form view
            eview = etree.fromstring(result["arch"])
            page_att = eview.xpath("//page[@name='product_attributes']")[0]
            page_att.append(notebook)

            result["arch"] = etree.tostring(eview, pretty_print=True)
        return result
