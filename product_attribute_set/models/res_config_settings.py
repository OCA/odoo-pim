# Copyright 2026 ForgeFlow (http://www.forgeflow.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attribute_set_show_native_everywhere = fields.Boolean(
        string="Native attributes on every product form",
        config_parameter="product_attribute_set.show_native_attributes_everywhere",
        help="When enabled, the native attributes belonging to a product's "
        "attribute set are shown in the Attributes tab whatever the menu "
        "(Sales, Inventory, Purchase...) used to open the product form. "
        "When disabled, only actions that set the "
        "'include_native_attribute_view_ref' context display them.",
    )
