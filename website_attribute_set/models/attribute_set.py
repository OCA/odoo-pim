# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from .mixins import bump_facet_cache_version


class AttributeSet(models.Model):
    _inherit = "attribute.set"

    def write(self, vals):
        res = super().write(vals)
        bump_facet_cache_version(self.env)
        return res

    def unlink(self):
        res = super().unlink()
        bump_facet_cache_version(self.env)
        return res
