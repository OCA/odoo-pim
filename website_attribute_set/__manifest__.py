# Copyright 2011 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Website Attribute Set",
    "version": "18.0.1.0.0",
    "category": "Website/Website",
    "license": "AGPL-3",
    "author": "Kencove, Odoo Community Association (OCA)",
    "maintainers": ["kobros-tech"],
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "attribute_set",
        "product_attribute_set",
        "pim",
        "website_sale",
    ],
    "data": [
        "views/attribute_attribute_view.xml",
        "views/variant_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [],
    },
    "installable": True,
    "application": True,
}
