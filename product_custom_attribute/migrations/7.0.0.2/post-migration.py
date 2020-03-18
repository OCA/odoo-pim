# Copyright 2013 Akretion (http://www.akretion.com).
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

logger = logging.getLogger("upgrade")


def migrate(cr, version):
    if version:  # do not run on a fresh DB, see lp:1259975
        logger.info(
            "Migrating product_custom_attribute from version %s", version
        )
        cr.execute(
            "UPDATE product_template pt "
            "SET attribute_set_id = (SELECT pp.attribute_set_id "
            "                        FROM product_product pp WHERE "
            "                        pp.product_tmpl_id = pt.id "
            "                        LIMIT 1)"
            "WHERE pt.attribute_set_id IS NULL"
        )
        cr.execute("ALTER TABLE product_product DROP COLUMN attribute_set_id")
