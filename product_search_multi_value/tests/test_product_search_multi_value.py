# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductSearchMultiValue(TransactionCase):
    def setUp(self):
        super(TestProductSearchMultiValue, self).setUp()
        self.default_code_list = ["E-COM08", "E-COM10", "E-COM06"]

    def test_search_multi_value(self):
        default_code_values = " ".join(self.default_code_list)

        domain = [("search_multi", "ilike", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, 3)

        domain = [("search_multi", "=", default_code_values)]
        res = self.env["product.template"].search_count(domain)
        self.assertEqual(res, 3)

        domain = [("search_multi", "not ilike", default_code_values)]
        with self.assertRaises(UserError):
            self.env["product.template"].search_count(domain)

        domain = [("search_multi", "!=", default_code_values)]
        with self.assertRaises(UserError):
            self.env["product.template"].search_count(domain)
