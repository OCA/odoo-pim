# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv.orm import setup_modifiers


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    @api.model
    def _build_attribute_field(self, vals):
        """Hide attributes fields which are not related to
        the product's attribute_set"""
        res = super(AttributeAttribute, self)._build_attribute_field(vals)
        context = self.env.context
        if context.get('product_custom_attribute'):
            parent = res.getparent()
            if len(parent) != 0:
                parent.set("attrs",
                           "{'invisible': [('attribute_set_id', 'not in', %s)]}"
                           % self.attribute_set_ids.ids
                           )
                setup_modifiers(parent)

        return res

    @api.model
    def _build_attributes_notebook(self, vals):
        """Hide page's attribute_group which have no attributes fields
        related to the product's attribute_set"""
        res = super(AttributeAttribute, self)._build_attributes_notebook(vals)
        context = self.env.context
        if context.get('product_custom_attribute'):
            for page in res:
                att_group = self.env['attribute.group'].search(
                    [('name', '=', page.get("string"))])
                att_set_ids = []
                for att in att_group.attribute_ids:
                    att_set_ids += [*att.attribute_set_ids.ids]
                domain = "[('attribute_set_id', 'not in', %s)]" % list(set(att_set_ids))
                page.set("attrs", "{\"invisible\": %s }" % domain)
                setup_modifiers(page)

        return res
