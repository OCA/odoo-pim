"""Extension to attribute.attribute for B-tree expression indexes.

This module extends the OCA attribute_set_jsonb module with B-tree index
support for range queries on numeric and date attributes.

Phase 3: B-tree indexes for range queries (>, <, >=, <=, BETWEEN)
"""

import logging
import re

from psycopg2 import Error as Psycopg2Error
from psycopg2 import sql

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Map attribute types to PostgreSQL cast types for B-tree indexes
BTREE_CAST_MAP = {
    "integer": "integer",
    "float": "numeric",
    "date": "date",
    "datetime": "timestamp",
}

# Attribute types that support B-tree range indexes
BTREE_SUPPORTED_TYPES = set(BTREE_CAST_MAP.keys())


def _is_jsonb_column(cr, table_name, column_name):
    """Check if a column exists and is of JSONB type.

    Args:
        cr: Database cursor
        table_name: Name of the table
        column_name: Name of the column

    Returns:
        bool: True if column exists and is JSONB, False otherwise
    """
    cr.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table_name, column_name),
    )
    result = cr.fetchone()
    return result and result[0] == "jsonb"


class AttributeAttribute(models.Model):
    """Extend attribute.attribute with B-tree index support for range queries."""

    _inherit = "attribute.attribute"

    index_type = fields.Selection(
        selection=[
            ("none", "No Index"),
            ("gin", "GIN (equality/containment)"),
            ("btree", "B-tree (range queries)"),
        ],
        default="none",
        help="GIN indexes are optimal for equality filters (=, in, ilike). "
        "B-tree indexes are required for range queries (>, <, BETWEEN) on "
        "numeric and date attributes. B-tree only works with integer, float, "
        "date, and datetime attribute types.",
    )

    @api.onchange("index_type")
    def _onchange_index_type(self):
        """Sync create_gin_index with index_type for backward compatibility."""
        if self.index_type == "gin":
            self.create_gin_index = True
        elif self.index_type == "none":
            self.create_gin_index = False
        # Note: btree doesn't set create_gin_index

    @api.onchange("create_gin_index")
    def _onchange_create_gin_index(self):
        """Sync index_type with create_gin_index for backward compatibility."""
        if self.create_gin_index and self.index_type == "none":
            self.index_type = "gin"
        elif not self.create_gin_index and self.index_type == "gin":
            self.index_type = "none"

    def _can_create_btree_index(self):
        """Check if this attribute can have a B-tree index.

        Returns:
            bool: True if attribute type supports B-tree indexing
        """
        self.ensure_one()
        return self.attribute_type in BTREE_SUPPORTED_TYPES

    def _is_column_jsonb(self):
        """Check if the serialization column is JSONB type.

        This is required for creating GIN or B-tree expression indexes.
        TEXT columns don't support GIN indexes without special operator classes.

        Returns:
            bool: True if column exists and is JSONB, False otherwise
        """
        self.ensure_one()

        if not self.serialized:
            return False

        table_name = self._get_table_name()
        jsonb_column = self._get_jsonb_column_name()

        if not table_name or not jsonb_column:
            return False

        return _is_jsonb_column(self.env.cr, table_name, jsonb_column)

    def _create_gin_expression_index(self):
        """Safely create a GIN index, checking column type first.

        This overrides/complements the parent's GIN index creation to ensure
        we only create GIN indexes on JSONB columns. TEXT columns don't have
        a default operator class for GIN access method.

        Returns:
            bool: True if index was created successfully
        """
        self.ensure_one()

        if not self.serialized:
            _logger.debug(
                "Skipping GIN index creation for non-serialized attribute %s",
                self.name,
            )
            return False

        if not self._is_column_jsonb():
            _logger.warning(
                "Cannot create GIN index for attribute %s: "
                "column is not JSONB type. Install base_sparse_field_jsonb first.",
                self.name,
            )
            return False

        # Call parent's GIN index creation if available
        if hasattr(super(), "_create_gin_expression_index"):
            return super()._create_gin_expression_index()

        # Fallback: Create GIN index directly
        table_name = self._get_table_name()
        jsonb_column = self._get_jsonb_column_name()
        index_name = f"idx_{table_name}_{self.name}_gin"

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
            _logger.info("GIN index %s already exists", index_name)
            return True

        try:
            create_index_query = sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {index}
                ON {table} USING GIN (({column}->{attr_name}))
                """
            ).format(
                index=sql.Identifier(index_name),
                table=sql.Identifier(table_name),
                column=sql.Identifier(jsonb_column),
                attr_name=sql.Literal(self.name),
            )
            cr.execute(create_index_query)
            _logger.info(
                "Created GIN expression index %s on %s.%s for attribute %s",
                index_name,
                table_name,
                jsonb_column,
                self.name,
            )
            return True
        except Psycopg2Error as e:
            _logger.warning(
                "Could not create GIN expression index %s: %s",
                index_name,
                e,
            )
            return False

    def _get_btree_index_name(self):
        """Generate a safe B-tree index name for this attribute.

        Returns:
            str: Index name in format idx_{table}_{field_name}_btree
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
        max_total = 63
        max_table_field = max_total - 11  # Allow for idx_ + _btree
        combined = f"{table_name}_{safe_name}"
        if len(combined) > max_table_field:
            combined = combined[:max_table_field]

        return f"idx_{combined}_btree"

    def _create_btree_expression_index(self):
        """Create a B-tree expression index for range queries.

        Creates an index like:
            CREATE INDEX idx_product_template_capacity_btree
            ON product_template (((x_custom_json_attrs->>'x_capacity')::numeric))
            WHERE x_custom_json_attrs ? 'x_capacity';

        B-tree indexes support range operators: >, <, >=, <=, BETWEEN
        Only works for numeric (integer, float) and date (date, datetime) types.

        Returns:
            bool: True if index was created successfully
        """
        self.ensure_one()

        if not self.serialized:
            _logger.debug(
                "Skipping B-tree index creation for non-serialized attribute %s",
                self.name,
            )
            return False

        if not self._can_create_btree_index():
            _logger.warning(
                "Cannot create B-tree index for attribute %s: "
                "type %s not supported. Use integer, float, date, or datetime.",
                self.name,
                self.attribute_type,
            )
            return False

        index_name = self._get_btree_index_name()
        table_name = self._get_table_name()
        jsonb_column = self._get_jsonb_column_name()
        cast_type = BTREE_CAST_MAP.get(self.attribute_type)

        if not all([index_name, table_name, jsonb_column, cast_type]):
            _logger.warning(
                "Cannot create B-tree index for attribute %s: missing required info",
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
            _logger.info("B-tree index %s already exists", index_name)
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
                "Table %s does not exist, skipping B-tree index creation",
                table_name,
            )
            return False

        # Check if column exists and is JSONB
        if not _is_jsonb_column(cr, table_name, jsonb_column):
            _logger.warning(
                "Column %s.%s does not exist or is not JSONB, "
                "skipping B-tree index creation",
                table_name,
                jsonb_column,
            )
            return False

        try:
            # Create B-tree expression index with proper type casting
            create_index_query = sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {index}
                ON {table} ((({column}->>{attr_name})::{cast_type}))
                WHERE {column} ? {attr_name}
                """
            ).format(
                index=sql.Identifier(index_name),
                table=sql.Identifier(table_name),
                column=sql.Identifier(jsonb_column),
                attr_name=sql.Literal(self.name),
                cast_type=sql.SQL(cast_type),
            )
            cr.execute(create_index_query)
            _logger.info(
                "Created B-tree expression index %s on %s.%s for attribute %s "
                "(type: %s, cast: %s)",
                index_name,
                table_name,
                jsonb_column,
                self.name,
                self.attribute_type,
                cast_type,
            )
            return True
        except Psycopg2Error as e:
            _logger.warning(
                "Could not create B-tree expression index %s: %s",
                index_name,
                e,
            )
            return False

    def _drop_btree_expression_index(self):
        """Drop the B-tree expression index for this attribute."""
        self.ensure_one()

        index_name = self._get_btree_index_name()
        if not index_name:
            return False

        cr = self.env.cr

        try:
            drop_index_query = sql.SQL("DROP INDEX IF EXISTS {index}").format(
                index=sql.Identifier(index_name),
            )
            cr.execute(drop_index_query)
            _logger.info("Dropped B-tree expression index %s", index_name)
            return True
        except Psycopg2Error as e:
            _logger.warning(
                "Could not drop B-tree expression index %s: %s",
                index_name,
                e,
            )
            return False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle index creation safely.

        We need to intercept GIN index creation to prevent errors on TEXT columns.
        The parent module's create_gin_index field triggers GIN index creation,
        but this fails if the column is not JSONB.
        """
        # Pre-process vals_list to block GIN index on non-JSONB columns
        # We need to check the target model's column type
        modified_vals_list = []
        for vals in vals_list:
            modified_vals = vals.copy()

            # Check if this record will try to create a GIN index
            wants_gin = vals.get("create_gin_index") or vals.get("index_type") == "gin"
            if wants_gin and vals.get("serialization_field_id"):
                # Get the serialization field to check column type
                ser_field = self.env["ir.model.fields"].browse(
                    vals["serialization_field_id"]
                )
                if ser_field.exists():
                    model_name = vals.get("model") or ser_field.model
                    if model_name:
                        table_name = model_name.replace(".", "_")
                        column_name = ser_field.name

                        if not _is_jsonb_column(self.env.cr, table_name, column_name):
                            # Block GIN index creation
                            modified_vals["create_gin_index"] = False
                            if vals.get("index_type") == "gin":
                                modified_vals["index_type"] = "none"
                            _logger.warning(
                                "Blocking GIN index for new attribute %s: "
                                "column %s.%s is not JSONB.",
                                vals.get("name", "unknown"),
                                table_name,
                                column_name,
                            )

            modified_vals_list.append(modified_vals)

        records = super().create(modified_vals_list)

        # Handle B-tree index creation after records are created
        for record in records:
            if record.serialized and record.index_type == "btree":
                record._create_btree_expression_index()

        return records

    def write(self, vals):
        """Override write to handle index creation/deletion safely.

        We intercept create_gin_index changes to prevent GIN index creation
        on TEXT columns, which would fail with 'no default operator class'.
        """
        # Track which records need index changes
        records_to_btree_index = self.env["attribute.attribute"]
        records_to_drop_btree_index = self.env["attribute.attribute"]
        records_blocked_gin = self.env["attribute.attribute"]

        # CRITICAL: Block GIN index creation on non-JSONB columns
        # The parent module will try to create GIN indexes which fails on TEXT
        block_gin_index = False
        if vals.get("create_gin_index"):
            for record in self.filtered(lambda r: r.serialized):
                if not record._is_column_jsonb():
                    records_blocked_gin |= record
                    block_gin_index = True
                    _logger.warning(
                        "Blocking GIN index for attribute %s: column is not JSONB. "
                        "Install base_sparse_field_jsonb to enable JSONB storage.",
                        record.name,
                    )

        # If any record would fail GIN index, temporarily disable it
        modified_vals = vals.copy() if block_gin_index else vals
        if block_gin_index:
            modified_vals["create_gin_index"] = False

        # Handle index_type changes
        if "index_type" in vals:
            new_type = vals["index_type"]
            for record in self.filtered(lambda r: r.serialized):
                old_type = record.index_type
                if old_type != new_type:
                    # Drop old B-tree index if switching away
                    if old_type == "btree":
                        records_to_drop_btree_index |= record
                    # Create new B-tree index if switching to
                    if new_type == "btree":
                        records_to_btree_index |= record
                    # Block GIN index if column is not JSONB
                    if new_type == "gin" and not record._is_column_jsonb():
                        records_blocked_gin |= record
                        modified_vals = (
                            modified_vals.copy()
                            if modified_vals is vals
                            else modified_vals
                        )
                        modified_vals["index_type"] = "none"
                        _logger.warning(
                            "Blocking GIN index_type for attribute %s: "
                            "column is not JSONB.",
                            record.name,
                        )

        result = super().write(modified_vals)

        # Handle B-tree index changes after write
        for record in records_to_drop_btree_index:
            record._drop_btree_expression_index()

        for record in records_to_btree_index:
            record._create_btree_expression_index()

        return result

    def unlink(self):
        """Override unlink to drop B-tree indexes before deletion."""
        for record in self:
            if record.serialized and record.index_type == "btree":
                record._drop_btree_expression_index()

        return super().unlink()

    def action_regenerate_all_indexes(self):
        """Extend to regenerate B-tree indexes as well."""
        # Call parent for GIN indexes
        result = super().action_regenerate_all_indexes()

        # Also handle B-tree indexes
        btree_attributes = self.search(
            [
                ("serialized", "=", True),
                ("index_type", "=", "btree"),
            ]
        )

        btree_created = 0
        btree_failed = 0
        for attr in btree_attributes:
            if attr._create_btree_expression_index():
                btree_created += 1
            else:
                btree_failed += 1

        if btree_created or btree_failed:
            _logger.info(
                "B-tree index regeneration: %d created, %d failed",
                btree_created,
                btree_failed,
            )
            # Update the notification message
            if result.get("params", {}).get("message"):
                result["params"]["message"] += (
                    f" B-tree: {btree_created} created, {btree_failed} failed."
                )

        return result
