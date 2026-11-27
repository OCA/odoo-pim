"""Cascading validation rules for conditional requirements."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AttributeValidationCascade(models.Model):
    """Define conditional validation rules based on other attribute values."""

    _name = "attribute.validation.cascade"
    _description = "Cascading Validation Rule"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # === Trigger Condition ===
    trigger_attribute_id = fields.Many2one(
        comodel_name="attribute.attribute",
        string="When Attribute",
        required=True,
        help="The attribute that triggers this cascade",
    )
    trigger_operator = fields.Selection(
        selection=[
            ("=", "Equals"),
            ("!=", "Not Equals"),
            ("in", "In List"),
            ("not in", "Not In List"),
            ("set", "Is Set (not empty)"),
            ("not_set", "Is Not Set (empty)"),
        ],
        required=True,
        default="=",
    )
    trigger_value = fields.Char(
        help="Value(s) to compare. For 'in'/'not in', use comma-separated values.",
    )

    # === Target Effect ===
    target_attribute_id = fields.Many2one(
        comodel_name="attribute.attribute",
        string="Then Attribute",
        required=True,
        help="The attribute affected by this cascade",
    )
    effect_type = fields.Selection(
        selection=[
            ("required", "Make Required"),
            ("optional", "Make Optional"),
            ("hidden", "Hide"),
            ("visible", "Show"),
            ("apply_rule", "Apply Validation Rule"),
            ("filter_values", "Filter Allowed Values"),
        ],
        required=True,
        default="required",
    )

    # === For apply_rule effect ===
    validation_rule_id = fields.Many2one(
        comodel_name="attribute.validation.rule",
        string="Validation Rule",
    )

    # === For filter_values effect ===
    filter_domain = fields.Char(
        help="Domain to filter dynamic source. Can use {trigger_value} placeholder.",
    )
    allowed_values_filter = fields.Char(
        help="Comma-separated list of allowed values when triggered",
    )

    # === Scope ===
    attribute_set_ids = fields.Many2many(
        comodel_name="attribute.set",
        string="Apply To Sets",
        help="Limit cascade to specific attribute sets. Empty = all.",
    )

    @api.constrains("trigger_attribute_id", "target_attribute_id")
    def _check_different_attributes(self):
        """Ensure trigger and target are different attributes."""
        for cascade in self:
            if cascade.trigger_attribute_id == cascade.target_attribute_id:
                raise ValidationError(
                    self.env._("Trigger and target attributes must be different.")
                )

    def evaluate(self, trigger_value, record=None):
        """
        Evaluate if this cascade rule should be applied.

        :param trigger_value: The current value of the trigger attribute
        :param record: Optional record context
        :return: tuple (should_apply: bool, effect_data: dict)
        """
        self.ensure_one()

        should_apply = False

        if self.trigger_operator == "=":
            should_apply = str(trigger_value or "") == str(self.trigger_value or "")
        elif self.trigger_operator == "!=":
            should_apply = str(trigger_value or "") != str(self.trigger_value or "")
        elif self.trigger_operator == "in":
            values = [v.strip() for v in (self.trigger_value or "").split(",")]
            should_apply = str(trigger_value or "") in values
        elif self.trigger_operator == "not in":
            values = [v.strip() for v in (self.trigger_value or "").split(",")]
            should_apply = str(trigger_value or "") not in values
        elif self.trigger_operator == "set":
            should_apply = bool(trigger_value)
        elif self.trigger_operator == "not_set":
            should_apply = not bool(trigger_value)

        if not should_apply:
            return False, {}

        effect_data = {
            "effect_type": self.effect_type,
            "target_attribute_id": self.target_attribute_id.id,
            "target_attribute_name": self.target_attribute_id.name,
        }

        if self.effect_type == "apply_rule" and self.validation_rule_id:
            effect_data["validation_rule_id"] = self.validation_rule_id.id
        elif self.effect_type == "filter_values":
            if self.filter_domain:
                # Replace placeholder with actual trigger value
                effect_data["filter_domain"] = self.filter_domain.replace(
                    "{trigger_value}", str(trigger_value or "")
                )
            if self.allowed_values_filter:
                effect_data["allowed_values"] = [
                    v.strip() for v in self.allowed_values_filter.split(",")
                ]

        return True, effect_data

    def get_cascade_effects_for_attribute(
        self, attribute_id, value, attribute_set_id=None
    ):
        """
        Get all cascade effects for a given attribute and value.

        :param attribute_id: The trigger attribute ID
        :param value: The current value of the trigger attribute
        :param attribute_set_id: Optional attribute set ID to filter cascades
        :return: list of effect dictionaries
        """
        domain = [
            ("trigger_attribute_id", "=", attribute_id),
            ("active", "=", True),
        ]
        cascades = self.search(domain)

        effects = []
        for cascade in cascades:
            # Check attribute set scope
            if attribute_set_id and cascade.attribute_set_ids:
                if attribute_set_id not in cascade.attribute_set_ids.ids:
                    continue

            should_apply, effect_data = cascade.evaluate(value)
            if should_apply:
                effects.append(effect_data)

        return effects
