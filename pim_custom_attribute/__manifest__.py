# Copyright 2015 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "PIM Custom Attributes",
    "version": "12.0.2.0.0",
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
    ],
    "demo": ["demo/product_attribute.xml"],
    "installable": True,
}
