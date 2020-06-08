# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MassObject(models.Model):

    _inherit = "mass.object"

    attribute_group_id = fields.Many2one("attribute.group", ondelete="cascade")
