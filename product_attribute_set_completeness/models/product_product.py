# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # The completeness is computed on the templates only, the variants read
    # the criteria fields from their template.

    @api.depends("product_tmpl_id.attribute_set_completion_rate")
    def _compute_attribute_set_completion_rate(self):
        for rec in self:
            rec.attribute_set_completion_rate = (
                rec.product_tmpl_id.attribute_set_completion_rate
            )

    @api.depends("product_tmpl_id.attribute_set_completion_state")
    def _compute_attribute_set_completion_state(self):
        for rec in self:
            rec.attribute_set_completion_state = (
                rec.product_tmpl_id.attribute_set_completion_state
            )
