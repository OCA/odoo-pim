# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Attribute Set Completeness",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV",
    "website": "https://acsone.eu",
    "depends": ["attribute_set"],
    "data": [
        "views/attribute_set.xml",
        "security/attribute_set_completeness.xml",
        "views/attribute_set_completeness.xml",
    ],
    "demo": [],
    "external_dependencies": {"python": ["odoo_test_helper"]},
}
