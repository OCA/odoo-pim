# Copyright 2022 Akretion
# @author: Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return

    # 14.0.1.3.0 adds field company_dependent
    # but ['ir.model']._instanciate_attrs is
    # run before the creation of the column
    # by the ORM
    cr.execute(
        "ALTER TABLE attribute_attribute ADD COLUMN IF NOT EXISTS company_dependent boolean"
    )
