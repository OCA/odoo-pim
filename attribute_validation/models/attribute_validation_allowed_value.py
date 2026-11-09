"""Static allowed values for validation rules."""

from odoo import fields, models


class AttributeValidationAllowedValue(models.Model):
    """Define static allowed values for a validation rule."""

    _name = "attribute.validation.allowed.value"
    _description = "Allowed Value for Validation Rule"
    _order = "sequence, value"

    rule_id = fields.Many2one(
        comodel_name="attribute.validation.rule",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    value = fields.Char(required=True)
    display_value = fields.Char(
        string="Display Label",
        help="Display label (if different from value)",
    )
    active = fields.Boolean(default=True)

    _rule_value_uniq = models.Constraint(
        "UNIQUE(rule_id, value)",
        "Value must be unique within a rule",
    )
