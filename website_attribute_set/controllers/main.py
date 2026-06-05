# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo.fields import Domain
from odoo.http import request
from odoo.models import BaseModel

from odoo.addons.website_sale.controllers import main

from ..models.mixins import (
    _parse_relational_id,
    _sparse_filter_by_value,
    build_range_filter_domains,
)


class WebsiteSale(main.WebsiteSale):
    def _parse_additional_attrib_values(self):
        """Parse additional_attribute_values params from the request.

        The JS handler (onChangeAttribute) groups all selected values for the
        same attribute into a single URL param by joining them with a comma:
          additional_attribute_values=42-val1,val2,val3

        This method splits them back so every (attr_id, value) pair is
        returned as a separate two-element list.
        """
        request_args = request.httprequest.args
        raw_list = request_args.getlist("additional_attribute_values")
        result = []
        for raw in raw_list:
            if not raw:
                continue
            first_dash = raw.index("-")
            attr_id = int(raw[:first_dash])
            for value in raw[first_dash + 1 :].split(","):
                if value:
                    result.append([attr_id, value])
        return result

    def _parse_additional_range_filters(self):
        """Parse additional_attr_min_/max_ params from the request."""
        request_args = request.httprequest.args
        range_filters = {}
        for key in request_args.keys():
            if key.startswith("additional_attr_min_"):
                attr_id = int(key.replace("additional_attr_min_", ""))
                if attr_id not in range_filters:
                    range_filters[attr_id] = {}
                try:
                    range_filters[attr_id]["min"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue
            elif key.startswith("additional_attr_max_"):
                attr_id = int(key.replace("additional_attr_max_", ""))
                if attr_id not in range_filters:
                    range_filters[attr_id] = {}
                try:
                    range_filters[attr_id]["max"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue
        return range_filters

    def _shop_get_query_url_kwargs(self, search, min_price, max_price, **post):
        result = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, **post
        )
        additional_attrib_list = request.httprequest.args.getlist(
            "additional_attribute_values"
        )
        if additional_attrib_list:
            result["additional_attribute_values"] = additional_attrib_list
        for key in request.httprequest.args.keys():
            if key.startswith("additional_attr_min_") or key.startswith(
                "additional_attr_max_"
            ):
                result[key] = request.httprequest.args[key]
        return result

    def _get_search_options(
        self,
        category=None,
        attribute_value_dict=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        values = super()._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        additional_attrib_values = self._parse_additional_attrib_values()
        if additional_attrib_values:
            values["additional_attribute_values"] = additional_attrib_values
        additional_range_filters = self._parse_additional_range_filters()
        if additional_range_filters:
            values["additional_range_filters"] = additional_range_filters
        return values

    def _get_additional_shop_values(self, values, **kwargs):
        """Hook to update values used for rendering website_sale.products template"""
        extra_values = super()._get_additional_shop_values(values, **kwargs)

        additional_attrib_values = self._parse_additional_attrib_values()
        additional_attrib_set = set(
            (item[0], item[1]) for item in additional_attrib_values
        )
        extra_values["additional_attrib_set"] = additional_attrib_set
        extra_values["additional_attributes"] = []

        search_product = values.get("search_product")
        if not search_product:
            return extra_values

        sudo_products = search_product.sudo()
        sudo_products.fetch(["attribute_set_id"])
        set_ids = {p.attribute_set_id.id for p in sudo_products if p.attribute_set_id}
        if not set_ids:
            return extra_values

        attrs_per_set = sudo_products._get_extra_attributes_per_set(list(set_ids))
        all_additional_attributes = request.env["attribute.attribute"].sudo()
        attr_ids_per_set = {}
        for sid, attrs in attrs_per_set.items():
            all_additional_attributes |= attrs
            attr_ids_per_set[sid] = set(attrs.ids)
        if not all_additional_attributes:
            return extra_values

        product_ids_per_attr = defaultdict(list)
        for product in sudo_products:
            sid = product.attribute_set_id.id
            if not sid:
                continue
            for attr_id in attr_ids_per_set.get(sid, ()):
                product_ids_per_attr[attr_id].append(product.id)

        for attribute in all_additional_attributes:
            attr_dict = self._build_additional_attribute_facet(
                attribute, sudo_products, product_ids_per_attr
            )
            if attr_dict is not None:
                extra_values["additional_attributes"].append(attr_dict)

        return extra_values

    def _build_additional_attribute_facet(
        self, attribute, sudo_products, product_ids_per_attr
    ):
        """Build the facet dict for a single additional attribute.

        Returns ``None`` when no product in the current shop result carries a
        value for ``attribute``, so the caller can skip it.
        """
        pids = product_ids_per_attr.get(attribute.id)
        if not pids:
            return None
        attr_type = attribute.attribute_type or attribute.ttype
        field_name = (
            f"{attribute.name}_filename"
            if attr_type in ("binary", "image")
            else attribute.name
        )
        attr_products = sudo_products.browse(pids)
        attr_products.mapped(field_name)
        all_attribute_values = set()
        value_counts = {}
        for product in attr_products:
            attribute_values = product[field_name]
            # For boolean, False is a valid filter value (not "no value").
            # For every other type, falsy means nothing is set.
            if not attribute_values and attr_type != "boolean":
                continue
            if isinstance(attribute_values, BaseModel) and len(attribute_values) > 1:
                for rec in attribute_values:
                    all_attribute_values.add(rec)
                    if attribute.e_com_show_count:
                        key = rec.id if hasattr(rec, "id") else rec
                        value_counts[key] = value_counts.get(key, 0) + 1
            else:
                all_attribute_values.add(attribute_values)
                if attribute.e_com_show_count:
                    key = (
                        attribute_values.id
                        if hasattr(attribute_values, "id")
                        else attribute_values
                    )
                    value_counts[key] = value_counts.get(key, 0) + 1
        attr_dict = {
            "attribute": attribute,
            "all_attribute_values": sorted(
                all_attribute_values,
                key=lambda v: v.display_name
                if hasattr(v, "display_name")
                else (
                    v
                    if isinstance(v, (int, float))
                    else str(v)
                    if v is not None
                    else ""
                ),
            ),
        }
        if attribute.e_com_show_count:
            attr_dict["value_counts"] = value_counts
        return attr_dict

    def _get_shop_domain(self, search, category, attribute_value_dict, **kwargs):
        """Extend shop domain with additional attribute filters."""
        domain = super()._get_shop_domain(
            search, category, attribute_value_dict, **kwargs
        )

        additional_attrib_values = self._parse_additional_attrib_values()
        additional_range_filters = self._parse_additional_range_filters()

        additional_conditions = []
        additional_conditions.extend(
            self._build_range_filter_conditions(additional_range_filters)
        )
        additional_conditions.extend(
            self._build_value_filter_conditions(additional_attrib_values)
        )

        if additional_conditions:
            return Domain.AND([domain] + additional_conditions)
        return domain

    def _build_range_filter_conditions(self, range_filters):
        """Build domain conditions for range filters (min/max)."""
        return build_range_filter_domains(request.env, range_filters)

    def _build_value_filter_conditions(self, attrib_values):
        """Build domain conditions for value filters (select, boolean, etc.)."""
        if not attrib_values:
            return []

        conditions = []
        Attribute = request.env["attribute.attribute"].sudo()

        attr_values_grouped = {}
        for attr_id, attr_value in attrib_values:
            attr_values_grouped.setdefault(attr_id, []).append(attr_value)

        for attr_id, values in attr_values_grouped.items():
            attribute = Attribute.browse(attr_id)
            if not attribute.exists() or not attribute.field_is_searchable:
                continue

            field_name = attribute.name
            attr_type = attribute.attribute_type
            field = request.env["product.template"]._fields.get(field_name)
            sparse_col = getattr(field, "sparse", None) if field else None
            if sparse_col:
                if len(values) > 1 and attribute.e_com_multi_select:
                    all_ids = []
                    for v in values:
                        all_ids.extend(
                            _sparse_filter_by_value(
                                request.env,
                                "product.template",
                                sparse_col,
                                field_name,
                                attr_type,
                                v,
                            )
                        )
                    if all_ids:
                        conditions.append([("id", "in", list(set(all_ids)))])
                else:
                    for attr_value in values:
                        ids = _sparse_filter_by_value(
                            request.env,
                            "product.template",
                            sparse_col,
                            field_name,
                            attr_type,
                            attr_value,
                        )
                        if ids:
                            conditions.append([("id", "in", ids)])
                continue

            if len(values) > 1 and attribute.e_com_multi_select:
                or_conds = [
                    c
                    for v in values
                    if (c := self._build_attribute_condition(field_name, attr_type, v))
                ]
                if or_conds:
                    conditions.append(Domain.OR(or_conds))
            else:
                for attr_value in values:
                    cond = self._build_attribute_condition(
                        field_name, attr_type, attr_value
                    )
                    if cond:
                        conditions.append(cond)
        return conditions

    def _build_attribute_condition(self, field_name, attr_type, attr_value):
        """Build a single domain condition for an attribute value."""
        if attr_type == "boolean":
            value = attr_value.lower() == "true"
            return [(field_name, "=", value)]
        elif attr_type in ("select", "multiselect"):
            # The URL value may be a plain integer string or the
            # 'name-{model}-id-{N}' format from the filter template.
            option_id = _parse_relational_id(attr_value)
            if option_id is None:
                return None
            return [(field_name, "=", option_id)]
        elif attr_type == "integer":
            try:
                value = int(attr_value)
                return [(field_name, "=", value)]
            except (ValueError, TypeError):
                return None
        elif attr_type == "float":
            try:
                value = float(attr_value)
                return [(field_name, "=", value)]
            except (ValueError, TypeError):
                return None
        else:
            return [(field_name, "=", attr_value)]

    def _prepare_product_values(self, product, category, **kwargs):
        vals = super()._prepare_product_values(product, category, **kwargs)
        vals["additional_attributes"] = []
        extra_attributes = product.sudo().get_extra_attributes()
        for attribute in extra_attributes:
            attribute_values = product.sudo().get_extra_attribute_values(attribute)
            if attribute_values:
                vals["additional_attributes"].append(
                    {"attribute": attribute, "attribute_values": attribute_values}
                )
        return vals
