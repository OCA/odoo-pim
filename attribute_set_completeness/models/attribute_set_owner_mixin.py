# Copyright 2020 ACSONE SA/NV
# Copyright 2021 Camptocamp (http://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeSetOwnerMixin(models.AbstractModel):
    _inherit = "attribute.set.owner.mixin"

    attribute_set_completeness_ids = fields.One2many(
        related="attribute_set_id.attribute_set_completeness_ids",
    )
    attribute_set_completed_ids = fields.Many2many(
        comodel_name="attribute.set.completeness",
        compute="_compute_attribute_set_completed_ids",
        string="Attribute Set completed criterias",
    )
    attribute_set_not_completed_ids = fields.Many2many(
        comodel_name="attribute.set.completeness",
        compute="_compute_attribute_set_not_completed_ids",
        string="Attribute Set not completed criterias",
    )
    attribute_set_completion_rate = fields.Float(
        compute="_compute_attribute_set_completion_rate",
        help="Attribute set completeness percentage",
        store=True,
    )
    attribute_set_completion_state = fields.Selection(
        selection=[("complete", "Complete"), ("not_complete", "Not complete")],
        compute="_compute_attribute_set_completion_state",
        help="Attribute set completeness status",
        store=True,
    )

    @api.depends("attribute_set_completeness_ids")
    def _compute_attribute_set_completed_ids(self):
        """Compute completed attribute set criterias"""
        for rec in self:
            rec.attribute_set_completed_ids = (
                rec.attribute_set_completeness_ids.filtered(
                    lambda c: bool(rec[c.field_id.name])
                )
            )

    @api.depends("attribute_set_completed_ids")
    def _compute_attribute_set_not_completed_ids(self):
        """Compute not completed attribute set criterias"""
        for rec in self:
            rec.attribute_set_not_completed_ids = (
                rec.attribute_set_completeness_ids - rec.attribute_set_completed_ids
            )

    @api.depends("attribute_set_completed_ids")
    def _compute_attribute_set_completion_rate(self):
        """Compute the completion rate from completed criterias"""
        for rec in self:
            rec.attribute_set_completion_rate = (
                sum(rec.attribute_set_completed_ids.mapped("completion_rate"))
                if rec.attribute_set_completed_ids
                else 0.0
            )

    @api.depends("attribute_set_completion_rate")
    def _compute_attribute_set_completion_state(self):
        """Compute the completion state"""
        for rec in self:
            rec.attribute_set_completion_state = (
                "complete"
                if rec.attribute_set_completion_rate >= 100.0
                else "not_complete"
            )
