"""Extension to attribute.attribute for website filtering."""

from odoo import api, fields, models


class AttributeAttribute(models.Model):
    """Extend attribute.attribute with website filtering configuration."""

    _inherit = "attribute.attribute"

    website_visible = fields.Boolean(
        string="Show in Website Filters",
        default=False,
        help="Display this attribute in website shop filters. "
        "Only applicable to serialized (JSONB) attributes.",
    )
    website_filter_type = fields.Selection(
        selection=[
            ("checkbox", "Checkbox"),
            ("select", "Dropdown"),
            ("range", "Range Slider"),
        ],
        string="Filter Display Type",
        default="checkbox",
        help="How to display this attribute in website filters. "
        "Range slider only works with numeric attributes that have B-tree indexes.",
    )
    website_sequence = fields.Integer(
        string="Website Filter Sequence",
        default=10,
        help="Order in which this attribute appears in website filters.",
    )

    @api.onchange("website_filter_type")
    def _onchange_website_filter_type(self):
        """Validate range filter type is only used with numeric attributes."""
        if self.website_filter_type == "range":
            if self.attribute_type not in ("integer", "float", "date", "datetime"):
                return {
                    "warning": {
                        "title": "Invalid Filter Type",
                        "message": "Range slider filter only works with numeric "
                        "(integer, float) or date (date, datetime) attributes. "
                        "Consider using checkbox or dropdown instead.",
                    }
                }
            if self.index_type != "btree":
                return {
                    "warning": {
                        "title": "Performance Warning",
                        "message": "Range filters work best with B-tree indexes. "
                        "Consider setting Index Type to 'B-tree (range queries)' "
                        "for better performance.",
                    }
                }
        return None

    def _get_distinct_values(self, domain=None):
        """Get distinct values for this serialized attribute.

        Args:
            domain: Optional domain to filter products

        Returns:
            list: Distinct values found in the database
        """
        self.ensure_one()

        if not self.serialized or not self.serialization_field_id:
            return []

        table_name = self.model.replace(".", "_")
        jsonb_column = self.serialization_field_id.name

        # Build WHERE clause from domain if provided
        where_clause = f"({jsonb_column})::jsonb ? %s"
        params = [self.name]

        # Add active filter for product.template
        if self.model == "product.template":
            where_clause += " AND active = true AND sale_ok = true"

        # Table/column names from trusted model fields, values are parameterized
        query = f"""
            SELECT DISTINCT ({jsonb_column})::jsonb->>%s as value
            FROM {table_name}
            WHERE {where_clause}
              AND ({jsonb_column})::jsonb->>%s IS NOT NULL
            ORDER BY value
        """  # nosec B608
        params.extend([self.name, self.name])

        self.env.cr.execute(query, params)
        return [row[0] for row in self.env.cr.fetchall() if row[0]]

    def _get_min_max_values(self, domain=None):
        """Get min and max values for numeric/date attributes.

        Args:
            domain: Optional domain to filter products

        Returns:
            tuple: (min_value, max_value) or (None, None) if not applicable
        """
        self.ensure_one()

        if not self.serialized or not self.serialization_field_id:
            return None, None

        if self.attribute_type not in ("integer", "float", "date", "datetime"):
            return None, None

        table_name = self.model.replace(".", "_")
        jsonb_column = self.serialization_field_id.name

        # Determine cast type
        cast_map = {
            "integer": "integer",
            "float": "numeric",
            "date": "date",
            "datetime": "timestamp",
        }
        cast_type = cast_map.get(self.attribute_type, "text")

        # Build WHERE clause
        where_clause = f"({jsonb_column})::jsonb ? %s"
        params = [self.name]

        # Add active filter for product.template
        if self.model == "product.template":
            where_clause += " AND active = true AND sale_ok = true"

        # Table/column/cast from trusted model fields, values are parameterized
        query = f"""
            SELECT
                MIN((({jsonb_column})::jsonb->>%s)::{cast_type}) as min_val,
                MAX((({jsonb_column})::jsonb->>%s)::{cast_type}) as max_val
            FROM {table_name}
            WHERE {where_clause}
        """  # nosec B608
        params.extend([self.name, self.name])

        self.env.cr.execute(query, params)
        row = self.env.cr.fetchone()
        if row:
            return row[0], row[1]
        return None, None

    def _get_facet_counts(self, base_domain=None):
        """Get value counts for this attribute within a filtered product set.

        Args:
            base_domain: Domain to filter products

        Returns:
            dict: {value: count} mapping
        """
        self.ensure_one()

        if not self.serialized or not self.serialization_field_id:
            return {}

        table_name = self.model.replace(".", "_")
        jsonb_column = self.serialization_field_id.name

        # Build WHERE clause
        where_clause = f"({jsonb_column})::jsonb ? %s"
        params = [self.name]

        # Add active filter for product.template
        if self.model == "product.template":
            where_clause += " AND active = true AND sale_ok = true"

        # Table/column names from trusted model fields, values are parameterized
        query = f"""
            SELECT
                ({jsonb_column})::jsonb->>%s as value,
                COUNT(*) as count
            FROM {table_name}
            WHERE {where_clause}
              AND ({jsonb_column})::jsonb->>%s IS NOT NULL
            GROUP BY ({jsonb_column})::jsonb->>%s
            ORDER BY count DESC
        """  # nosec B608
        params.extend([self.name, self.name, self.name])

        self.env.cr.execute(query, params)
        return {row[0]: row[1] for row in self.env.cr.fetchall() if row[0]}
