# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.expression import AND, FALSE_DOMAIN, OR
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):

    _inherit = "product.template"

    search_multi = fields.Char(
        "Multiple search", compute="_compute_search_multi", search="_search_multi"
    )

    @api.multi
    def _compute_search_multi(self):
        self.search_multi = False

    @api.multi
    def _search_multi(self, operator, value):
        default_res = FALSE_DOMAIN
        if operator in ["=", "ilike"]:
            operator = "in"
            comparator = OR
        elif operator in ["!=", "not ilike"]:
            operator = "not in"
            comparator = AND
        else:
            return default_res
        value_list = value.split(" ") if " " in value else [value]

        search_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("product_search_multi_value.search_fields")
        )
        search_fields = safe_eval(search_fields)

        domain_list = []
        for search_field in search_fields:
            domain_search_field = [(search_field, operator, value_list)]
            domain_list.append(domain_search_field)

        return comparator(domain_list)
