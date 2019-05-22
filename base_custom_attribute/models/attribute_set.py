# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeSet(models.Model):
    _name = "attribute.set"
    _description = "Attribute Set"

    name = fields.Char("Name", required=True, translate=True)

    attribute_group_ids = fields.One2many(
        "attribute.group", "attribute_set_id", "Attribute Groups"
    )

    model_id = fields.Many2one("ir.model", "Model", required=True)
