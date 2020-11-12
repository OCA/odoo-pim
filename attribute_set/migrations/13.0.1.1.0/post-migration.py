# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Set many2many tag widget"""
    _logger.info("Init attribute widget")
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        attributes = env["attribute.attribute"].search([("ttype", "=", "many2many")])
        attributes.write({"widget": "many2many_tags"})
