# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from difflib import SequenceMatcher

from odoo import api, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


def search_extra(env, search_term):
    extra_domains = []
    attributes = (
        env["attribute.attribute"].sudo().search([("e_com_searchable", "=", True)])
    )
    for attribute in attributes:
        if attribute.attribute_type in ["char", "text"]:
            extra_domain = [(attribute.name, "ilike", search_term)]
            extra_domains.append(extra_domain)
        elif attribute.attribute_type in ["integer", "float"]:
            try:
                if attribute.attribute_type == "integer":
                    extra_domain = [(attribute.name, "ilike", int(search_term))]
                    extra_domains.append(extra_domain)
                elif attribute.attribute_type == "float":
                    extra_domain = [(attribute.name, "ilike", float(search_term))]
                    extra_domains.append(extra_domain)
            except ValueError as e:
                _logger.debug("Non-numeric search term for %s: %s", attribute.name, e)
        elif attribute.relation_model_id and attribute.attribute_type in [
            "select",
            "multiselect",
        ]:
            extra_domain = [(f"{attribute.name}.name", "ilike", search_term)]
            extra_domains.append(extra_domain)
        else:
            similarity = (
                SequenceMatcher(None, attribute.field_description, search_term).ratio()
                * 100
            )
            if similarity > 80:
                extra_domain = [(attribute.name, "!=", False)]
                extra_domains.append(extra_domain)
    return Domain.OR(extra_domains)


class WebsiteSearchableMixin(models.AbstractModel):
    _inherit = "website.searchable.mixin"

    @api.model
    def _search_fetch(self, search_detail, search, limit, order):
        results, count = super()._search_fetch(
            search_detail=search_detail, search=search, limit=limit, order=order
        )
        model = self.sudo() if search_detail.get("requires_sudo") else self
        if model._name == "product.template":
            fields = search_detail["search_fields"]
            base_domain = search_detail["base_domain"]
            domain = self._search_build_domain(
                base_domain, search, fields, search_extra
            )
            results = model.search(
                domain, limit=limit, order=search_detail.get("order", order)
            )
            count = model.search_count(domain)
        return results, count
