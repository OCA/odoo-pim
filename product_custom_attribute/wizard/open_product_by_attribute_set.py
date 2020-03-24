# Copyright 2015 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class OpenProductByAttributeSet(models.TransientModel):
    _name = "open.product.by.attribute.set"
    _description = "Wizard to open product by attributes set"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.multi
    def open_product_by_attribute_set(self):
        """
        Opens Product by attributes
        @return: dictionary of Product list window for a given attributes set
        """
        self.ensure_one()

        result = self.env.ref("product.product_template_action_all")
        result = result.read()[0]

        attribute_set = self.attribute_set_id

        # TODO : isn't it possible to simplify this return dict ?
        result.update(
            {
                "context": "{'open_product_by_attribute_set': %s, \
                'attribute_set_id': %s}"
                % (True, attribute_set.id),
                "domain": "[('attribute_set_id', '=', %s)]" % attribute_set.id,
                "name": attribute_set.name,
            }
        )
        return result
