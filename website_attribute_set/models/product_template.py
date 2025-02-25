# Copyright 2011 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_extra_attribute_values(self, extra_attribute=None):
        self.ensure_one()
        extra_attribute_values = None
        if extra_attribute:
            rec_value = getattr(self, extra_attribute.name)
            if rec_value:
                extra_attribute_values = rec_value

        return extra_attribute_values
