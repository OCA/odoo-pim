# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ProductSearchMultiMixin(models.AbstractModel):
    _name = "product.search.multi.mixin"
    _description = "Product search multi value mixin"

    search_multi = fields.Char(
        "Multiple search",
        compute="_compute_search_multi",
        search="_search_multi",
    )

    def _compute_search_multi(self):
        self.update({"search_multi": False})

    @api.model
    def _get_search_fields(self):
        try:
            search_fields = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("product_search_multi_value.search_fields")
            )
            return safe_eval(search_fields)
        except SyntaxError as error:
            _logger.error("Error while evaluating search fields")
            _logger.error(error)
            return []

    def _search_multi(self, operator, value):
        if operator == "=" or operator == "ilike":
            operator = "in"
            comparator = OR
        else:
            raise UserError(_("Operator %s is not usable with multisearch", operator))

        value_list = value.split(" ") if " " in value else [value]
        search_fields = self._get_search_fields()
        domain_list = []
        for search_field in search_fields:
            domain_search_field = [(search_field, operator, tuple(value_list))]
            domain_list.append(domain_search_field)
        return comparator(domain_list)


class ProductTemplate(models.Model):
    _inherit = ["product.template", "product.search.multi.mixin"]
    _name = "product.template"


class ProductProduct(models.Model):
    _inherit = ["product.product", "product.search.multi.mixin"]
    _name = "product.product"
