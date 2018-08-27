# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AttributeSet(models.Model):
    _name = "attribute.set"
    _description = "Attribute Set"

    name = fields.Char(
        'Name',
        required=True,
        translate=True,
    )

    attribute_group_ids = fields.One2many(
        'attribute.group',
        'attribute_set_id',
        'Attribute Groups',
    )

    @api.model
    def _get_default_model(self):
        force_model = self.env.context.get('force_model')

        if force_model:
            models = self.env['ir.model'].search([
                ('model', '=', force_model)])

            if models:
                return models[0]

        return False

    model_id = fields.Many2one(
        'ir.model',
        'Model',
        required=True,
        default=_get_default_model,
    )
