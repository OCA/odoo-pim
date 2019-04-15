# -*- coding: utf-8 -*-
# Copyright 2015 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "Product Custom Attributes",
    "version": "10.0.0.0.1",
    "category": "Generic Modules/Others",
    "license": "AGPL-3",
    "author": "Akretion",
    "website": "https://akretion.com",
    "depends": ["product", "base_custom_attribute", "sale"],
    "data": [
        "views/attribute_set.xml",
        "views/attribute_group.xml",
        "views/attribute_attribute.xml",
        "views/product.xml",
        "views/product_category.xml",
        "wizard/open_product_by_attribute_set.xml",
        "wizard/product_product.xml",
    ],
    "demo": ["demo/product_attribute.xml"],
    "installable": True,
}
