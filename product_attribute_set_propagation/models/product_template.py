# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_propagatable_attributes = fields.Boolean(
        compute="_compute_has_propagatable_attributes",
        compute_sudo=True,
    )

    @api.depends("attribute_set_id", "attribute_set_id.attribute_ids")
    def _compute_has_propagatable_attributes(self):
        for record in self:
            if not record.attribute_set_id or not record.attribute_set_id.attribute_ids:
                record.has_propagatable_attributes = False
                continue
            record.has_propagatable_attributes = any(
                a.model == "product.template"
                for a in record.attribute_set_id.attribute_ids
            )

    def action_open_attribute_propagation_wizard(self):
        self.ensure_one()
        return {
            "name": _("Propagate Attributes"),
            "type": "ir.actions.act_window",
            "res_model": "product.attribute.propagation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_product_tmpl_id": self.id,
                "default_propagation_model": "product.template",
            },
        }
