# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Product Attribute Set Propagation",
    "summary": "Propagate attribute set values from one product to others",
    "version": "16.0.1.0.0",
    "category": "PIM",
    "license": "AGPL-3",
    "author": "ForgeFlow,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": ["product_attribute_set"],
    "data": [
        "security/ir.model.access.csv",
        "views/attribute_attribute_views.xml",
        "wizard/product_attribute_propagation_wizard_views.xml",
        "views/product_views.xml",
    ],
    "installable": True,
}
