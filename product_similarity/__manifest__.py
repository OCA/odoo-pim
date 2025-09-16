# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Products Similarity",
    "summary": "Enables to compute a similarity score between "
    "products using vectorial embeddings",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": ["product"],
    "data": [
        "views/product_vector_characteristic.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
}
