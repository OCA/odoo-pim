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
        string="Attribute Set completed criteria",
    )
    attribute_set_not_completed_ids = fields.Many2many(
        comodel_name="attribute.set.completeness",
        compute="_compute_attribute_set_not_completed_ids",
        string="Attribute Set not completed criteria",
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

    def _attribute_set_completeness_specs(self, rules):
        """Return the (field name, completion rate) of the given rules, to
        evaluate them on many records without browsing the rules again."""
        return [
            (rule.field_id.name, rule.completion_rate)
            for rule in rules
            if rule.field_id.name in self._fields
        ]

    @api.depends("attribute_set_completeness_ids.field_id")
    def _compute_attribute_set_completed_ids(self):
        """Compute completed attribute set criteria"""
        for attr_set, records in self.grouped("attribute_set_id").items():
            rules = attr_set.attribute_set_completeness_ids
            rule_fnames = [
                (rule.id, rule.field_id.name)
                for rule in rules
                if rule.field_id.name in self._fields
            ]
            for rec in records:
                rec.attribute_set_completed_ids = rules.browse(
                    [rule_id for rule_id, fname in rule_fnames if rec[fname]]
                )

    @api.depends("attribute_set_completed_ids")
    def _compute_attribute_set_not_completed_ids(self):
        """Compute not completed attribute set criteria"""
        for rec in self:
            rec.attribute_set_not_completed_ids = (
                rec.attribute_set_completeness_ids - rec.attribute_set_completed_ids
            )

    @api.depends(
        "attribute_set_completeness_ids.field_id",
        "attribute_set_completeness_ids.completion_rate",
    )
    def _compute_attribute_set_completion_rate(self):
        """Compute the completion rate from completed criteria"""
        for attr_set, records in self.grouped("attribute_set_id").items():
            specs = records._attribute_set_completeness_specs(
                attr_set.attribute_set_completeness_ids
            )
            for rec in records:
                rec.attribute_set_completion_rate = sum(
                    rate for fname, rate in specs if rec[fname]
                )

    @api.depends("attribute_set_completeness_ids", "attribute_set_completion_rate")
    def _compute_attribute_set_completion_state(self):
        """Compute the completion state"""
        for attr_set, records in self.grouped("attribute_set_id").items():
            has_rules = bool(attr_set.attribute_set_completeness_ids)
            for rec in records:
                if not has_rules:
                    rec.attribute_set_completion_state = False
                elif rec.attribute_set_completion_rate >= 100.0:
                    rec.attribute_set_completion_state = "complete"
                else:
                    rec.attribute_set_completion_state = "not_complete"

    def write(self, vals):
        res = super().write(vals)
        self._attribute_set_completeness_modified(vals.keys())
        return res

    def _attribute_set_completeness_modified(self, fnames):
        """Trigger the completeness recomputation of the records for which one
        of the given fields is a completeness criterion.

        The fields of the criteria depend on the attribute set of each record,
        so they can't be declared as compute dependencies.
        """
        fnames = set(fnames)
        records = self.browse()
        for attr_set, set_records in self.grouped("attribute_set_id").items():
            if fnames & set(
                attr_set.attribute_set_completeness_ids.field_id.mapped("name")
            ):
                records |= set_records
        if records:
            records.modified(["attribute_set_completeness_ids"])
        return records
