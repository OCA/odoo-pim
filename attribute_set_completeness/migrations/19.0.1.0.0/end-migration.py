# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL


def migrate(cr, version):
    """Records without completeness criteria no longer have a completion
    state, so that they are not considered as 'not complete'."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for model in env.registry.values():
        field = model._fields.get("attribute_set_completion_state")
        if model._abstract or not model._auto or not field or not field.store:
            continue
        cr.execute(
            SQL(
                """
                UPDATE %(table)s rec
                   SET attribute_set_completion_state = NULL
                 WHERE attribute_set_completion_state IS NOT NULL
                   AND NOT EXISTS (
                       SELECT 1 FROM attribute_set_completeness c
                        WHERE c.attribute_set_id = rec.attribute_set_id
                   )
                """,
                table=SQL.identifier(model._table),
            )
        )
