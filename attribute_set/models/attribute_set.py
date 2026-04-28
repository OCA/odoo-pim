# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AttributeSet(models.Model):
    _name = "attribute.set"
    _description = "Attribute Set"
    _parent_name = "parent_id"
    _parent_store = True

    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one(
        comodel_name="attribute.set",
        string="Parent Set",
        index=True,
        ondelete="restrict",
        domain="[('model_id', '=', model_id)]",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name="attribute.set",
        inverse_name="parent_id",
        string="Child Sets",
    )

    attribute_ids = fields.Many2many(
        comodel_name="attribute.attribute",
        string="Attributes",
        relation="rel_attribute_set",
        column1="attribute_set_id",
        column2="attribute_id",
    )
    complete_attribute_ids = fields.Many2many(
        comodel_name="attribute.attribute",
        string="All Attributes (inherited)",
        compute="_compute_complete_attribute_ids",
        recursive=True,
    )
    model_id = fields.Many2one("ir.model", "Model", required=True, ondelete="cascade")
    model = fields.Char(
        related="model_id.model",
        string="Model Name",
        store=True,
        help="This is a technical field in order to build filters on this one to avoid"
        "access on ir.model",
    )

    @api.depends("attribute_ids", "parent_id.complete_attribute_ids")
    def _compute_complete_attribute_ids(self):
        for rec in self:
            attributes = rec.attribute_ids
            parent = rec.parent_id
            while parent:
                attributes |= parent.attribute_ids
                parent = parent.parent_id
            rec.complete_attribute_ids = attributes

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(
                self.env._("Error! You cannot create recursive attribute sets.")
            )

    @api.constrains("parent_id", "model_id")
    def _check_parent_model(self):
        for rec in self:
            if rec.parent_id and rec.parent_id.model_id != rec.model_id:
                raise ValidationError(
                    self.env._(
                        "The parent attribute set must belong to the same"
                        " model as the child."
                    )
                )
