# Copyright 2015 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class OpenProductByAttributeSet(models.TransientModel):
    _name = "open.product.by.attribute.set"
    _description = "Wizard to open product by attributes set"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.multi
    def button_open_product_by_attribute_set(self):
        """
        Opens Products of a selected Attribute Set
        """
        self.ensure_one()

        act_product_tmpl_all = self.env.ref(
            "product.product_template_action_all").read()[0]
        act_product_tmpl_all['context'] = "{\
            'search_default_attribute_set_id' : %s}" % self.attribute_set_id.id

        return act_product_tmpl_all
