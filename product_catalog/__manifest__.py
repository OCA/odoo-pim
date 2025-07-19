# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Catalog Attribute Set",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Kencove, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "depends": [
        "product",
        "sale",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/product_views.xml",
    ],
    "installable": True,
    "application": True,
}
