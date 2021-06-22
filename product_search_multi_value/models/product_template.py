# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):

    _inherit = "product.template"

    search_multi = fields.Char(
        "Multiple search",
        compute="_compute_search_multi",
        search="_search_multi",
    )

    def _compute_search_multi(self):
        self.search_multi = False

    def _search_multi(self, operator, value):
        if operator == "=" or operator == "ilike":
            operator = "in"
            comparator = OR
        else:
            raise UserError(_("Operator %s is not usable with multisearch", operator))

        value_list = value.split(" ") if " " in value else [value]

        search_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("product_search_multi_value.search_fields")
        )
        search_fields = safe_eval(search_fields)

        domain_list = []
        for search_field in search_fields:
            domain_search_field = [(search_field, operator, tuple(value_list))]
            domain_list.append(domain_search_field)
        return comparator(domain_list)
