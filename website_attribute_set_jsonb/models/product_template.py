"""Extension to product.template for JSONB attribute filtering."""

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Extend product.template with JSONB attribute filtering methods."""

    _inherit = "product.template"

    @api.model
    def _get_jsonb_attribute_domain(self, attribute_filters):
        """Build domain for JSONB attribute filtering.

        This method translates JSONB attribute filter parameters into
        SQL-compatible domain expressions that can be used in searches.

        Args:
            attribute_filters: dict of {attribute_name: [values]} for equality
                              or {attribute_name: {'min': x, 'max': y}} for range

        Returns:
            list: Domain expression compatible with Odoo ORM
        """
        if not attribute_filters:
            return []

        # Get the serialization field name for product.template
        # This is typically 'x_custom_json_attrs' from attribute_set
        serialization_field = self.env["ir.model.fields"].search(
            [
                ("model", "=", "product.template"),
                ("ttype", "=", "serialized"),
            ],
            limit=1,
        )

        if not serialization_field:
            _logger.warning("No serialized field found on product.template")
            return []

        jsonb_column = serialization_field.name

        # Build list of product IDs that match all filters
        # This is more efficient than building complex domains
        matching_ids = self._get_jsonb_filtered_product_ids(
            attribute_filters, jsonb_column
        )

        if matching_ids is None:
            # No filters applied
            return []
        elif not matching_ids:
            # Filters applied but no matches
            return [("id", "=", 0)]  # Impossible domain
        else:
            return [("id", "in", matching_ids)]

    @api.model
    def _get_jsonb_filtered_product_ids(self, attribute_filters, jsonb_column):
        """Get product IDs matching JSONB attribute filters.

        Uses PostgreSQL JSONB operators for efficient filtering.

        Args:
            attribute_filters: Filter dict
            jsonb_column: Name of the JSONB column

        Returns:
            list: Matching product IDs, or None if no filters
        """
        if not attribute_filters:
            return None

        conditions = []
        params = []

        for attr_name, filter_value in attribute_filters.items():
            if isinstance(filter_value, dict):
                # Range filter: {'min': x, 'max': y}
                min_val = filter_value.get("min")
                max_val = filter_value.get("max")

                if min_val is not None:
                    conditions.append(f"(({jsonb_column})::jsonb->>%s)::numeric >= %s")
                    params.extend([attr_name, min_val])

                if max_val is not None:
                    conditions.append(f"(({jsonb_column})::jsonb->>%s)::numeric <= %s")
                    params.extend([attr_name, max_val])

            elif isinstance(filter_value, list):
                # Equality filter: [value1, value2, ...]
                if len(filter_value) == 1:
                    conditions.append(f"({jsonb_column})::jsonb->>%s = %s")
                    params.extend([attr_name, filter_value[0]])
                elif len(filter_value) > 1:
                    placeholders = ", ".join(["%s"] * len(filter_value))
                    conditions.append(
                        f"({jsonb_column})::jsonb->>%s IN ({placeholders})"
                    )
                    params.append(attr_name)
                    params.extend(filter_value)

        if not conditions:
            return None

        where_clause = " AND ".join(conditions)
        # Where clause uses %s placeholders, actual values are in params list
        query = f"""
            SELECT id FROM product_template
            WHERE active = true
              AND sale_ok = true
              AND {where_clause}
        """  # nosec B608

        self.env.cr.execute(query, params)
        return [row[0] for row in self.env.cr.fetchall()]

    @api.model
    def get_website_jsonb_attributes(self):
        """Get all website-visible JSONB attributes for filtering.

        Returns:
            recordset: attribute.attribute records configured for website filtering
        """
        return self.env["attribute.attribute"].search(
            [
                ("model", "=", "product.template"),
                ("serialized", "=", True),
                ("website_visible", "=", True),
            ],
            order="website_sequence, name",
        )
