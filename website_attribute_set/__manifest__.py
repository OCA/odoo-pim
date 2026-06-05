# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Website Attribute Set",
    "version": "19.0.1.1.4",
    "category": "Website/Website",
    "license": "AGPL-3",
    "author": "Kencove, Odoo Community Association (OCA)",
    "maintainers": ["kobros-tech"],
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "attribute_set",
        "product_attribute_set",
        "pim",
        "website",
        "website_sale",
        "website_sale_comparison",
    ],
    "data": [
        "views/attribute_attribute_view.xml",
        "views/variant_templates.xml",
        "views/templates.xml",
        "views/website_sale_comparison_template.xml",
        "views/pim_view.xml",
    ],
    "demo": [
        "demo/website_attribute_demo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_attribute_set/static/src/interactions/**/*",
        ],
    },
    "installable": True,
    "application": True,
}
