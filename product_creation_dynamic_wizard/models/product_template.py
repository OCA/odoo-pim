# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import api, models
from odoo.tools import str2bool


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _update_cache(self, values, validate=True):
        """Update the cache of ``self`` with ``values``.

        :param values: dict of field values, in any format.
        :param validate: whether values must be checked
        """
        if self.env.context.get("product_creation_wizard", False):
            values = {
                key: value
                for key, value in values.items()
                if not key.startswith("current_")
            }
        return super()._update_cache(values, validate=validate)

    def action_open_product_creation_dynamic_wizard(self):
        return self.env["product.creation.dynamic.wizard"].create({}).get_next_action()

    @api.model
    def load_views(self, views, options=None):
        result = super().load_views(views, options=options)
        self._disable_create_button(result.get("fields_views", {}))
        return result

    @api.model
    def _disable_create_button(self, views):
        if str2bool(
            self.env["ir.config_parameter"].get_param(
                "product_creation_dynamic_wizard.disable_create_product_button",
                default="False",
            ),
            default=False,
        ):
            for view in views.values():
                doc = etree.fromstring(view["arch"])
                doc.attrib.update({"create": "0"})
                view["arch"] = etree.tostring(doc, encoding="unicode")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_open_product_creation_dynamic_wizard(self):
        return self.env["product.creation.dynamic.wizard"].create({}).get_next_action()

    @api.model
    def load_views(self, views, options=None):
        result = super().load_views(views, options=options)
        self.env["product.template"]._disable_create_button(
            result.get("fields_views", {})
        )
        return result
