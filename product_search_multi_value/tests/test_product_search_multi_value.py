# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.osv.expression import TRUE_DOMAIN
from odoo.tests.common import TransactionCase


class TestProductSearchMultiValue(TransactionCase):
    def setUp(self):
        super(TestProductSearchMultiValue, self).setUp()
        self.default_code_list = [
            "FURN_7800",
            "FURN_7888",
            "FURN_8855",
        ]

    def test_search_multi_value(self):
        total_products = self.env["product.template"].search_count(TRUE_DOMAIN)
        default_code_values = " ".join(self.default_code_list)

        domain = [("search_multi", "ilike", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, 3)

        domain = [("search_multi", "=", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, 3)

        domain = [("search_multi", "not ilike", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, total_products - 3)

        domain = [("search_multi", "!=", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, total_products - 3)
