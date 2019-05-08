# -*- coding: utf-8 -*-
# Copyright 2015 Akretion (http://www.akretion.com).
# @author Benoit Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class OpenProductByAttributeSet(models.TransientModel):
    _name = "open.product.by.attribute.set"
    _description = "Wizard to open product by attributes set"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.multi
    def open_product_by_attribute(self):
        """
        Opens Product by attributes
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Product list window for a given attributes set
        """
        self.ensure_one()

        result = self.env.ref("product.product_template_action_all")
        result = result.read()[0]

        attribute_set = self.attribute_set_id

        grp_ids = (
            self.env["attribute.group"]
            .search([("attribute_set_id", "=", attribute_set.id)])
            .ids
        )

        result.update(
            {
                "context": "{'open_product_by_attribute_set': %s, \
                'attribute_group_ids': %s}"
                % (True, grp_ids),
                "domain": "[('attribute_set_id', '=', %s)]" % attribute_set.id,
                "name": attribute_set.name,
            }
        )
        return result
