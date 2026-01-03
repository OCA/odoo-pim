"""Installation hooks for attribute_set_jsonb.

The post_init_hook handles migration of attribute_set's serialized field
columns from TEXT to JSONB and creates GIN indexes for filtering.
"""

import logging

from psycopg2 import Error as Psycopg2Error
from psycopg2 import sql

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post-installation hook to migrate attribute_set columns to JSONB.

    This hook specifically targets the x_custom_json_attrs columns used by
    attribute_set for serialized attribute storage.
    """
    cr = env.cr

    _logger.info("attribute_set_jsonb: Starting post-install migration...")

    # Find all x_custom_json_attrs columns (attribute_set's serialization field)
    cr.execute(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE column_name = 'x_custom_json_attrs'
        ORDER BY table_name
        """
    )
    columns_to_migrate = cr.fetchall()

    migrated_count = 0
    index_count = 0

    for table_name, column_name, data_type in columns_to_migrate:
        # Migrate TEXT to JSONB if needed
        if data_type == "text":
            _logger.info(
                "Migrating %s.%s from TEXT to JSONB...", table_name, column_name
            )
            try:
                alter_query = sql.SQL(
                    """
                    ALTER TABLE {table}
                    ALTER COLUMN {column}
                    TYPE jsonb
                    USING CASE
                        WHEN {column} IS NULL THEN NULL
                        WHEN {column} = '' THEN '{{}}'::jsonb
                        ELSE {column}::jsonb
                    END
                    """
                ).format(
                    table=sql.Identifier(table_name),
                    column=sql.Identifier(column_name),
                )
                cr.execute(alter_query)
                migrated_count += 1
                _logger.info(
                    "Successfully migrated %s.%s to JSONB", table_name, column_name
                )
            except Psycopg2Error as e:
                _logger.warning(
                    "Could not migrate %s.%s to JSONB: %s", table_name, column_name, e
                )
                cr.rollback()
                continue

        # Create GIN index if not exists
        index_name = f"idx_{table_name}_{column_name}_gin"
        cr.execute(
            """
            SELECT 1 FROM pg_indexes
            WHERE tablename = %s AND indexname = %s
            """,
            (table_name, index_name),
        )
        if not cr.fetchone():
            _logger.info("Creating GIN index on %s.%s...", table_name, column_name)
            try:
                create_index_query = sql.SQL(
                    """
                    CREATE INDEX IF NOT EXISTS {index}
                    ON {table} USING GIN ({column})
                    """
                ).format(
                    index=sql.Identifier(index_name),
                    table=sql.Identifier(table_name),
                    column=sql.Identifier(column_name),
                )
                cr.execute(create_index_query)
                index_count += 1
                _logger.info("Created GIN index %s", index_name)
            except Psycopg2Error as e:
                _logger.warning(
                    "Could not create GIN index on %s.%s: %s",
                    table_name,
                    column_name,
                    e,
                )

    _logger.info(
        "attribute_set_jsonb: Migration complete. "
        "Migrated %d columns, created %d GIN indexes.",
        migrated_count,
        index_count,
    )
