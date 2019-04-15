# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    field_description = fields.Char(
        "Field Label", required=True, translate=True
    )
