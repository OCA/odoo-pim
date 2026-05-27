# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re
from difflib import SequenceMatcher

from odoo import api, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

# Matches the 'name-{model.name}-id-{N}' format emitted by select/multiselect
# filter templates, e.g. 'name-attribute.option-id-7'.
_RE_RELATIONAL_ID = re.compile(r"-id-(\d+)$")


def _parse_relational_id(attr_value):
    """Return the integer record ID from a filter value string.

    Handles both a plain integer string (``'7'``) and the
    ``'name-{model}-id-{N}'`` format produced by the select/multiselect
    filter templates.  Returns ``None`` if neither form can be parsed.
    """
    try:
        return int(attr_value)
    except (ValueError, TypeError):
        m = _RE_RELATIONAL_ID.search(str(attr_value))
        return int(m.group(1)) if m else None


def _sparse_search_ilike(env, model_name, sparse_col, field_name, search_term):
    table = env[model_name]._table
    env.cr.execute(
        f"SELECT id FROM {table} WHERE {sparse_col}::jsonb ->> %s ILIKE %s",
        (field_name, f"%{search_term}%"),
    )
    return [row[0] for row in env.cr.fetchall()]


_SPARSE_CAST = {
    "integer": ("integer", int),
    "float": ("numeric", float),
}


def _sparse_filter_by_value(
    env, model_name, sparse_col, field_name, attr_type, attr_value
):
    table = env[model_name]._table
    try:
        # Relational types store IDs; the URL value may be either a plain
        # integer string or the 'name-{model}-id-{N}' template format.
        if attr_type in ("select", "multiselect"):
            option_id = _parse_relational_id(attr_value)
            if option_id is None:
                return []
            if attr_type == "multiselect":
                # many2many: stored as a JSON array of IDs
                sql = (
                    f"SELECT id FROM {table}"
                    f" WHERE ({sparse_col}::jsonb -> %s)"
                    f" @> jsonb_build_array(%s::integer)"
                )
            else:
                # select (many2one): stored as a single integer ID
                sql = (
                    f"SELECT id FROM {table}"
                    f" WHERE ({sparse_col}::jsonb ->> %s)::integer = %s"
                )
            env.cr.execute(sql, (field_name, option_id))
            return [row[0] for row in env.cr.fetchall()]
        if attr_type == "boolean":
            value = str(attr_value).lower() == "true"
            if value:
                sql = (
                    f"SELECT id FROM {table}"
                    f" WHERE ({sparse_col}::jsonb ->> %s)::boolean = TRUE"
                )
                env.cr.execute(sql, (field_name,))
            else:
                sql = (
                    f"SELECT id FROM {table}"
                    f" WHERE ({sparse_col}::jsonb -> %s) IS NULL"
                    f"    OR ({sparse_col}::jsonb ->> %s)::boolean = FALSE"
                )
                env.cr.execute(sql, (field_name, field_name))
            return [row[0] for row in env.cr.fetchall()]
        cast_info = _SPARSE_CAST.get(attr_type)
        if cast_info:
            cast_type, coerce = cast_info
            sql = (
                f"SELECT id FROM {table}"
                f" WHERE ({sparse_col}::jsonb ->> %s)::{cast_type} = %s"
            )
            value = coerce(attr_value)
        else:
            sql = f"SELECT id FROM {table} WHERE {sparse_col}::jsonb ->> %s = %s"
            value = str(attr_value)
        env.cr.execute(sql, (field_name, value))
        return [row[0] for row in env.cr.fetchall()]
    except (ValueError, TypeError):
        return []


def _sparse_filter_by_range(env, model_name, sparse_col, field_name, range_vals):
    table = env[model_name]._table
    parts = []
    params = []
    if "min" in range_vals:
        parts.append(f"({sparse_col}::jsonb ->> %s)::numeric >= %s")
        params += [field_name, range_vals["min"]]
    if "max" in range_vals:
        parts.append(f"({sparse_col}::jsonb ->> %s)::numeric <= %s")
        params += [field_name, range_vals["max"]]
    if not parts:
        return []
    env.cr.execute(
        f"SELECT id FROM {table} WHERE {' AND '.join(parts)}",
        params,
    )
    return [row[0] for row in env.cr.fetchall()]


def search_extra(env, search_term):
    extra_domains = []
    attributes = (
        env["attribute.attribute"].sudo().search([("e_com_searchable", "=", True)])
    )
    product_template_fields = env["product.template"]._fields
    for attribute in attributes:
        field = product_template_fields.get(attribute.name)
        sparse_col = getattr(field, "sparse", None) if field else None
        if not field or not (field.store or field.search or sparse_col):
            _logger.debug(
                "Skipping non-searchable field %s in e-commerce search", attribute.name
            )
            continue
        if sparse_col:
            if attribute.attribute_type in ["char", "text"]:
                ids = _sparse_search_ilike(
                    env, "product.template", sparse_col, attribute.name, search_term
                )
                if ids:
                    extra_domains.append([("id", "in", ids)])
            continue
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
        model = self.sudo() if search_detail.get("requires_sudo") else self
        if model._name != "product.template":
            return super()._search_fetch(
                search_detail=search_detail, search=search, limit=limit, order=order
            )
        # For product.template we extend the standard search with extra attribute
        # domains (including sparse/serialized fields handled via raw JSONB queries).
        # Calling super() first would fail when base_domain already contains
        # conditions on sparse fields, so we build and run the domain ourselves.
        fields = search_detail["search_fields"]
        base_domain = search_detail["base_domain"]
        domain = self._search_build_domain(base_domain, search, fields, search_extra)
        results = model.search(
            domain, limit=limit, order=search_detail.get("order", order)
        )
        count = (
            model.search_count(domain)
            if limit and limit == len(results)
            else len(results)
        )
        return results, count
