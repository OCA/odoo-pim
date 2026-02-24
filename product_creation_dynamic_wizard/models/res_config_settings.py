from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    disable_create_product_button = fields.Boolean(
        "Disable create product button",
        config_parameter="product_creation_dynamic_wizard.disable_create_product_button",
    )
