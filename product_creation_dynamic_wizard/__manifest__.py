# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product creation dynamic wizard",
    "version": "17.0.1.0.0",
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
        "web",
    ],
    "data": [
        "wizards/product_creation_dynamic_wizard.xml",
        "views/assets.xml",
        "views/product_creation_question.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/product_creation_question.xml",
    ],
    "qweb": [
        "static/src/xml/tree_button.xml",
        "static/src/xml/kanban_button.xml",
        "static/src/xml/form_button.xml",
    ],
    "installable": True,
    "application": False,
}
