# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Information Management base",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "author": "Akretion, Pierre Verkest <pierre@verkest.fr>, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "product",
    ],
    "data": [
        "data/ir_module_category_data.xml",
        "security/pim_security.xml",
        "views/product_view.xml",
        "views/pim_view.xml",
        "views/product_attribute_value.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
}
