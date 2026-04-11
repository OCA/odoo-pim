# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Domain
from odoo.http import request
from odoo.models import BaseModel

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    def _parse_additional_attrib_values(self):
        """Parse additional_attribute_values params from the request."""
        request_args = request.httprequest.args
        raw_list = request_args.getlist("additional_attribute_values")
        parsed = [[x for x in v.split("-", maxsplit=1)] for v in raw_list if v]
        return [[int(sublist[0]), sublist[1]] for sublist in parsed]

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
        all_additional_attributes = request.env["attribute.attribute"].sudo()
        product_attrs_map = {}
        if search_product:
            for product in search_product:
                additional_attributes = product.sudo().get_extra_attributes()
                if additional_attributes:
                    product_attrs_map[product.id] = additional_attributes
                    all_additional_attributes |= additional_attributes

            if all_additional_attributes:
                for attribute in all_additional_attributes:
                    all_attribute_values = set()
                    value_counts = {}

                    for product in search_product:
                        if attribute not in product_attrs_map.get(product.id, []):
                            continue
                        attribute_values = product.sudo().get_extra_attribute_values(
                            attribute
                        )
                        if attribute_values:
                            if (
                                isinstance(attribute_values, BaseModel)
                                and len(attribute_values) > 1
                            ):
                                for rec in attribute_values:
                                    all_attribute_values.add(rec)
                                    if attribute.e_com_show_count:
                                        key = rec.id if hasattr(rec, "id") else rec
                                        value_counts[key] = value_counts.get(key, 0) + 1
                            else:
                                all_attribute_values.add(attribute_values)
                                if attribute.e_com_show_count:
                                    if hasattr(attribute_values, "id"):
                                        key = attribute_values.id
                                    else:
                                        key = attribute_values
                                    value_counts[key] = value_counts.get(key, 0) + 1

                    attr_dict = {
                        "attribute": attribute,
                        "all_attribute_values": list(all_attribute_values),
                    }
                    if attribute.e_com_show_count:
                        attr_dict["value_counts"] = value_counts
                    extra_values["additional_attributes"].append(attr_dict)

        return extra_values

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
        conditions = []
        Attribute = request.env["attribute.attribute"].sudo()
        for attr_id, range_vals in range_filters.items():
            attribute = Attribute.browse(attr_id)
            if not attribute.exists():
                continue
            field_name = attribute.name
            if "min" in range_vals:
                conditions.append((field_name, ">=", range_vals["min"]))
            if "max" in range_vals:
                conditions.append((field_name, "<=", range_vals["max"]))
        return conditions

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
            if not attribute.exists():
                continue

            field_name = attribute.name
            attr_type = attribute.attribute_type

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
            try:
                option_id = int(attr_value)
                return [(field_name, "=", option_id)]
            except (ValueError, TypeError):
                return None
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
