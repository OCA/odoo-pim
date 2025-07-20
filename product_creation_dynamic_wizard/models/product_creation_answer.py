# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductCreationAnswer(models.Model):
    _name = "product.creation.answer"
    _description = "Product creation answer"

    _order = "sequence"

    question_id = fields.Many2one(
        "product.creation.question",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True)
    sequence = fields.Integer(required=True, default=10)
