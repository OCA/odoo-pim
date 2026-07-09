"""Extension to attribute.attribute for expression-based GIN indexes.

This module adds the ability to create expression-based GIN indexes on
individual serialized attributes for optimized filtering performance.
"""

import logging
import re

from psycopg2 import Error as Psycopg2Error
from psycopg2 import sql

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AttributeAttribute(models.Model):
    """Extend attribute.attribute with expression-based GIN index support."""

    _inherit = "attribute.attribute"

    create_gin_index = fields.Boolean(
        string="Create Expression Index",
        default=False,
        help="Create an expression-based index for this attribute. "
        "Recommended for frequently filtered serialized attributes. "
        "This creates an index on the extracted JSON value for faster queries.",
    )

    def _get_index_name(self):
        """Generate a safe index name for this attribute.

        Returns:
            str: Index name in format idx_{table}_{field_name}_expr
        """
        self.ensure_one()
        if not self.serialization_field_id or not self.model:
            return None

        # Get table name from model
        table_name = self.model.replace(".", "_")

        # Sanitize field name (remove x_ prefix for readability)
        field_name = self.name
        if field_name.startswith("x_"):
            field_name = field_name[2:]

        # Ensure name is safe for PostgreSQL identifier
        safe_name = re.sub(r"[^a-z0-9_]", "", field_name.lower())

        # PostgreSQL has a 63-character limit for identifiers
        # idx_ (4) + table + _ (1) + field + _expr (5) = 10 + table + field
        max_total = 63
        max_table_field = max_total - 10
        combined = f"{table_name}_{safe_name}"
        if len(combined) > max_table_field:
            combined = combined[:max_table_field]

        return f"idx_{combined}_expr"

    def _get_table_name(self):
        """Get the PostgreSQL table name for this attribute's model."""
        self.ensure_one()
        if not self.model:
            return None
        return self.model.replace(".", "_")

    def _get_jsonb_column_name(self):
        """Get the JSONB column name for this attribute."""
        self.ensure_one()
        if not self.serialization_field_id:
            return None
        return self.serialization_field_id.name

    def _create_expression_index(self):
        """Create an expression-based index for this attribute.

        Creates an index like:
            CREATE INDEX idx_product_template_color_expr
            ON product_template ((x_custom_json_attrs->>'x_color'))
            WHERE x_custom_json_attrs ? 'x_color';
        """
        self.ensure_one()

        if not self.serialized:
            _logger.debug(
                "Skipping index creation for non-serialized attribute %s",
                self.name,
            )
            return False

        index_name = self._get_index_name()
        table_name = self._get_table_name()
        jsonb_column = self._get_jsonb_column_name()

        if not all([index_name, table_name, jsonb_column]):
            _logger.warning(
                "Cannot create index for attribute %s: missing required info",
                self.name,
            )
            return False

        cr = self.env.cr

        # Check if index already exists
        cr.execute(
            """
            SELECT 1 FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            """,
            (table_name, index_name),
        )
        if cr.fetchone():
            _logger.info("Index %s already exists", index_name)
            return True

        # Check if table exists
        cr.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s
            """,
            (table_name,),
        )
        if not cr.fetchone():
            _logger.warning(
                "Table %s does not exist, skipping index creation",
                table_name,
            )
            return False

        # Check if column exists
        cr.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table_name, jsonb_column),
        )
        if not cr.fetchone():
            _logger.warning(
                "Column %s.%s does not exist, skipping index creation",
                table_name,
                jsonb_column,
            )
            return False

        try:
            # Create expression-based index with partial index condition
            # This index is optimal for equality queries on extracted values
            create_index_query = sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {index}
                ON {table} (({column}->>{attr_name}))
                WHERE {column} ? {attr_name}
                """
            ).format(
                index=sql.Identifier(index_name),
                table=sql.Identifier(table_name),
                column=sql.Identifier(jsonb_column),
                attr_name=sql.Literal(self.name),
            )
            cr.execute(create_index_query)
            _logger.info(
                "Created expression index %s on %s.%s for attribute %s",
                index_name,
                table_name,
                jsonb_column,
                self.name,
            )
            return True
        except Psycopg2Error as e:
            _logger.warning(
                "Could not create expression index %s: %s",
                index_name,
                e,
            )
            return False

    def _drop_expression_index(self):
        """Drop the expression-based index for this attribute."""
        self.ensure_one()

        index_name = self._get_index_name()
        if not index_name:
            return False

        cr = self.env.cr

        try:
            drop_index_query = sql.SQL("DROP INDEX IF EXISTS {index}").format(
                index=sql.Identifier(index_name),
            )
            cr.execute(drop_index_query)
            _logger.info("Dropped expression index %s", index_name)
            return True
        except Psycopg2Error as e:
            _logger.warning(
                "Could not drop expression index %s: %s",
                index_name,
                e,
            )
            return False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle index creation."""
        records = super().create(vals_list)

        for record in records:
            if record.create_gin_index and record.serialized:
                record._create_expression_index()

        return records

    def write(self, vals):
        """Override write to handle index creation/deletion."""
        # Track which records need index changes
        records_to_index = self.env["attribute.attribute"]
        records_to_drop_index = self.env["attribute.attribute"]

        if "create_gin_index" in vals:
            if vals["create_gin_index"]:
                # Will need to create indexes for serialized attributes
                records_to_index = self.filtered(lambda r: r.serialized)
            else:
                # Will need to drop indexes
                records_to_drop_index = self.filtered(
                    lambda r: r.create_gin_index and r.serialized
                )

        result = super().write(vals)

        # Handle index changes after write
        for record in records_to_index:
            record._create_expression_index()

        for record in records_to_drop_index:
            record._drop_expression_index()

        return result

    def unlink(self):
        """Override unlink to drop indexes before deletion."""
        for record in self:
            if record.create_gin_index and record.serialized:
                record._drop_expression_index()

        return super().unlink()

    def action_regenerate_all_indexes(self):
        """Regenerate all expression indexes for serialized attributes.

        This action can be triggered manually to recreate all indexes,
        useful after database migration or recovery.
        """
        attributes = self.search(
            [
                ("create_gin_index", "=", True),
                ("serialized", "=", True),
            ]
        )

        created = 0
        failed = 0
        for attr in attributes:
            if attr._create_expression_index():
                created += 1
            else:
                failed += 1

        _logger.info(
            "Index regeneration complete: %d created, %d failed",
            created,
            failed,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Index Regeneration Complete",
                "message": f"Created {created} indexes, {failed} failed.",
                "type": "success" if failed == 0 else "warning",
            },
        }
