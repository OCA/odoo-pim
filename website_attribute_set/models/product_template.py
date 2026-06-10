# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_extra_attribute_values(self, extra_attribute=None):
        self.ensure_one()
        if extra_attribute:
            return self[extra_attribute.name] if self[extra_attribute.name] else None
        return None
