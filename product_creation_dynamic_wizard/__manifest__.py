# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product creation dynamic wizard",
    "version": "14.0.0.0.1",
    "license": "AGPL-3",
    "author": "Pierre Verkest <pierre@verkest.fr>, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "maintainers": [
        "petrus-v",
    ],
    "depends": [
        "product",
        "pim_base",
        "base_sparse_field",
    ],
    "data": [
        "wizards/product_creation_dynamic_wizard.xml",
        "views/product_template.xml",
        "views/product_creation_question.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/product_creation_question.xml",
    ],
    "installable": True,
    "application": False,
}
