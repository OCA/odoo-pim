# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Information Management",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "product",
        "product_attribute_set",
        "product_attribute_set_completeness",
    ],
    "data": [
        "data/ir_module_category_data.xml",
        "security/pim_security.xml",
        "views/product_view.xml",
        "views/pim_view.xml",
        "views/attribute_set.xml",
        "views/attribute_group.xml",
        "views/attribute_attribute.xml",
        "views/product_attribute_value.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
}
