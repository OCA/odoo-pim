# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AttributeGroup(models.Model):
    _name = "attribute.group"
    _description = "Attribute Group"
    _order = "sequence"

    name = fields.Char(
        'Name',
        size=128,
        required=True,
        translate=True
    )

    sequence = fields.Integer('Sequence')

    attribute_set_id = fields.Many2one(
        'attribute.set',
        'Attribute Set'
    )

    attribute_ids = fields.One2many(
        'attribute.location',
        'attribute_group_id',
        'Attributes'
    )

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

    @api.model
    def create(self, vals):
        for attribute in vals.get('attribute_ids', []):
            if (
                vals.get('attribute_set_id') and
                attribute[2] and
                not attribute[2].get('attribute_set_id')
            ):
                attribute[2]['attribute_set_id'] = vals['attribute_set_id']

        return super(AttributeGroup, self).create(vals)
