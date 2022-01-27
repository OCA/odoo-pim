# Copyright 2022 Acsone SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# when migrating to v14, 2 fields have been renamed
# completion_rate -> attribute_set_completion_rate
# completion_state -> attribute_set_completion_state
from openupgradelib import openupgrade

field_renames = [
    (
        "attribute.set.owner.mixin",
        "attribute.set.owner.mixin",
        "completion_rate",
        "attribute_set_completion_rate",
    ),
    (
        "attribute.set.owner.mixin",
        "attribute.set.owner.mixin",
        "completion_state",
        "attribute_set_completion_state",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, field_renames)
