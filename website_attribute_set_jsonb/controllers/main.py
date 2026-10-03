"""Website Sale controller extension for JSONB attribute filtering."""

import logging

from odoo import http
from odoo.fields import Domain
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleJsonb(WebsiteSale):
    def _shop_get_query_url_kwargs(
        self, search_or_category, search=None, min_price=None, max_price=None, **kwargs
    ):
        """Override to fix website_attribute_set bug passing extra category arg.

        The OCA website_attribute_set module incorrectly calls this method with
        category as the first argument. This override handles both signatures:
        - Base Odoo: _shop_get_query_url_kwargs(search, min_price, max_price, ...)
        - OCA: _shop_get_query_url_kwargs(category, search, min_price, max_price, ...)
        """
        # Detect if called with the buggy OCA signature (5 positional args)
        if search is not None:
            # Called with (category, search, min_price, max_price, **kwargs)
            # Ignore category and use correct params
            actual_search = search
            actual_min_price = min_price or 0.0
            actual_max_price = max_price or 0.0
        else:
            # Called with standard signature (search, min_price, max_price, **kwargs)
            actual_search = search_or_category
            actual_min_price = kwargs.pop("min_price", 0.0)
            actual_max_price = kwargs.pop("max_price", 0.0)

        return super()._shop_get_query_url_kwargs(
            actual_search, actual_min_price, actual_max_price, **kwargs
        )

    def _get_search_domain(
        self, search, category, attrib_values, search_in_description=True
    ):
        """Extend search domain to include JSONB attribute filters.

        This method is called by /shop route to build the product search domain.
        We extend it to include JSONB attribute filters from URL parameters.
        """
        domain = super()._get_search_domain(
            search, category, attrib_values, search_in_description
        )

        # Get JSONB attribute filters from request
        jsonb_filters = self._parse_jsonb_attribute_params()
        if jsonb_filters:
            jsonb_domain = request.env["product.template"]._get_jsonb_attribute_domain(
                jsonb_filters
            )
            if jsonb_domain:
                domain = Domain.AND([domain, jsonb_domain])

        return domain

    def _parse_jsonb_attribute_params(self):
        """Parse JSONB attribute filter parameters from request.

        URL format:
            Equality filters: ?jsonb_x_color=red,blue&jsonb_x_brand=caterpillar
            Range filters: ?jsonb_range_x_capacity=1000-5000

        Returns:
            dict: {attribute_name: [values]} or {attribute_name: {'min': x, 'max': y}}
        """
        filters = {}

        for key, value in request.httprequest.args.items():
            if not value:
                continue

            if key.startswith("jsonb_range_"):
                # Range filter
                attr_name = key[12:]  # Remove 'jsonb_range_' prefix
                if "-" in value:
                    parts = value.split("-", 1)
                    try:
                        min_val = float(parts[0]) if parts[0] else None
                        max_val = float(parts[1]) if parts[1] else None
                        filters[attr_name] = {"min": min_val, "max": max_val}
                    except ValueError:
                        _logger.warning(
                            "Invalid range value for %s: %s", attr_name, value
                        )
                        continue

            elif key.startswith("jsonb_"):
                # Equality filter
                attr_name = key[6:]  # Remove 'jsonb_' prefix
                values = [v.strip() for v in value.split(",") if v.strip()]
                if values:
                    filters[attr_name] = values

        return filters

    def _get_jsonb_attribute_values(self):
        """Get current JSONB attribute filter values from request.

        Returns:
            dict: {attribute_name: [selected_values]} for template rendering
        """
        return self._parse_jsonb_attribute_params()

    @http.route()
    def shop(
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        """Extend shop route to include JSONB attributes in context."""
        response = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post,
        )

        # Add JSONB attribute data to the response values
        if hasattr(response, "qcontext"):
            # Get website-visible JSONB attributes
            jsonb_attributes = request.env[
                "product.template"
            ].get_website_jsonb_attributes()

            # Get current filter selections
            selected_jsonb_values = self._get_jsonb_attribute_values()

            # Prepare attribute data with distinct values and facet counts
            jsonb_attr_data = []
            for attr in jsonb_attributes:
                attr_info = {
                    "attribute": attr,
                    "values": [],
                    "selected": selected_jsonb_values.get(attr.name, []),
                    "filter_type": attr.website_filter_type,
                }

                if attr.website_filter_type == "range":
                    # Get min/max for range slider
                    min_val, max_val = attr._get_min_max_values()
                    attr_info["min_value"] = min_val
                    attr_info["max_value"] = max_val

                    # Get current range selection
                    range_selection = selected_jsonb_values.get(attr.name)
                    if isinstance(range_selection, dict):
                        attr_info["selected_min"] = range_selection.get("min")
                        attr_info["selected_max"] = range_selection.get("max")
                else:
                    # Get distinct values with counts for checkbox/select
                    distinct_values = attr._get_distinct_values()
                    facet_counts = attr._get_facet_counts()

                    attr_info["values"] = [
                        {
                            "value": val,
                            "count": facet_counts.get(val, 0),
                            "selected": val in attr_info["selected"],
                        }
                        for val in distinct_values
                    ]

                jsonb_attr_data.append(attr_info)

            response.qcontext["jsonb_attributes"] = jsonb_attr_data
            response.qcontext["selected_jsonb_values"] = selected_jsonb_values

        return response

    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        pricelist=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        """Extend search options to preserve JSONB filter parameters."""
        options = super()._get_search_options(
            category=category,
            attrib_values=attrib_values,
            pricelist=pricelist,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )

        # Add JSONB filter params to preserve them in pagination/sorting
        jsonb_filters = self._parse_jsonb_attribute_params()
        if jsonb_filters:
            jsonb_params = {}
            for attr_name, filter_value in jsonb_filters.items():
                if isinstance(filter_value, dict):
                    # Range filter
                    min_val = filter_value.get("min", "")
                    max_val = filter_value.get("max", "")
                    jsonb_params[f"jsonb_range_{attr_name}"] = f"{min_val}-{max_val}"
                else:
                    # Equality filter
                    jsonb_params[f"jsonb_{attr_name}"] = ",".join(filter_value)

            options["jsonb_filters"] = jsonb_params

        return options
