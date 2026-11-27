# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools import SQL, sql

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Create the columns of the stored completeness fields on the tables of
    the existing attribute set owners, so that they don't get computed record
    by record on install. There is no completeness rule yet, so the
    completion rate is 0 and there is no completion state."""
    cr = env.cr
    model_names = env.registry.descendants(["attribute.set.owner.mixin"], "_inherit")
    for model_name in model_names:
        model = env[model_name]
        field = model._fields.get("attribute_set_id")
        if (
            model._abstract
            or not model._auto
            or not field
            or not field.store
            or not sql.table_exists(cr, model._table)
        ):
            continue
        table = SQL.identifier(model._table)
        if not sql.column_exists(cr, model._table, "attribute_set_completion_rate"):
            _logger.info("Create attribute_set_completion_rate on %s", model._table)
            # A constant default doesn't rewrite the table
            cr.execute(
                SQL(
                    "ALTER TABLE %s ADD COLUMN attribute_set_completion_rate"
                    " float8 DEFAULT 0",
                    table,
                )
            )
            cr.execute(
                SQL(
                    "ALTER TABLE %s ALTER COLUMN attribute_set_completion_rate"
                    " DROP DEFAULT",
                    table,
                )
            )
        if not sql.column_exists(cr, model._table, "attribute_set_completion_state"):
            _logger.info("Create attribute_set_completion_state on %s", model._table)
            sql.create_column(
                cr, model._table, "attribute_set_completion_state", "varchar"
            )
