# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Catalog Attribute Set",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Kencove, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "web",
        "product",
        "pim",
        "website_attribute_set",
    ],
    "data": [
        "views/product_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "product_catalog_attribute_set/static/src/search_model.esm.js",
            "product_catalog_attribute_set/static/src/kanban_model.esm.js",
            "product_catalog_attribute_set/static/src/search_panel.xml",
            "product_catalog_attribute_set/static/src/search_panel.esm.js",
        ],
    },
    "installable": True,
    "application": True,
}
