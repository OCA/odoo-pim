# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AttributeLocation(models.Model):
    _name = "attribute.location"
    _description = "Attribute Location"
    _order = "sequence"
    _inherits = {"attribute.attribute": "attribute_id"}

    attribute_id = fields.Many2one(
        "attribute.attribute",
        "Product Attribute",
        required=True,
        ondelete="cascade",
    )

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        related="attribute_group_id.attribute_set_id",
        readonly=True,
    )

    attribute_group_id = fields.Many2one(
        "attribute.group", "Attribute Group", required=True, ondelete="cascade"
    )

    sequence = fields.Integer("Sequence")
