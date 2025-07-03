# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(
        env.cr,
        [
            (
                "pim.module_category_pim",
                "pim_base.module_category_pim",
            ),
            (
                "pim.group_pim_reader",
                "pim_base.group_pim_reader",
            ),
            (
                "pim.group_pim_user",
                "pim_base.group_pim_user",
            ),
            (
                "pim.group_pim_manager",
                "pim_base.group_pim_manager",
            ),
        ],
    )
