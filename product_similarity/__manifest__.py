# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Products Similarity",
    "summary": "Define the product characteristics used to compute "
    "a similarity vector between products",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/product_field_vectorization_wizard.xml",
        "views/product_vector_characteristic.xml",
    ],
}
