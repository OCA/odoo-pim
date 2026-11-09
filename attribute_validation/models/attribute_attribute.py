"""Extension to attribute.attribute for validation support."""

from odoo import api, fields, models


class AttributeAttribute(models.Model):
    """Extend attribute.attribute with validation capabilities."""

    _inherit = "attribute.attribute"

    validation_rule_ids = fields.Many2many(
        comodel_name="attribute.validation.rule",
        relation="attribute_validation_rule_rel",
        column1="attribute_id",
        column2="rule_id",
        string="Validation Rules",
        help="Rules to validate values for this attribute",
    )
    cascade_trigger_ids = fields.One2many(
        comodel_name="attribute.validation.cascade",
        inverse_name="trigger_attribute_id",
        string="Triggers Cascades",
        help="Cascade rules triggered by changes to this attribute",
    )
    cascade_target_ids = fields.One2many(
        comodel_name="attribute.validation.cascade",
        inverse_name="target_attribute_id",
        string="Affected By Cascades",
        help="Cascade rules that affect this attribute",
    )
    enable_autocomplete = fields.Boolean(
        help="Show autocomplete suggestions from validation rules",
    )
    validation_rule_count = fields.Integer(
        compute="_compute_validation_rule_count",
        string="# Rules",
    )

    @api.depends("validation_rule_ids")
    def _compute_validation_rule_count(self):
        for attribute in self:
            attribute.validation_rule_count = len(attribute.validation_rule_ids)

    def validate_value(self, value, record=None):
        """
        Validate a value against all rules for this attribute.

        :param value: The value to validate
        :param record: Optional record context for python expressions
        :return: tuple (is_valid: bool, errors: list of str)
        """
        self.ensure_one()
        errors = []

        for rule in self.validation_rule_ids.filtered("active"):
            is_valid, error = rule.validate(value, record)
            if not is_valid and error:
                errors.append(error)

        return len(errors) == 0, errors

    def get_autocomplete_values(self, search_term="", limit=50):
        """
        Get autocomplete values from all applicable rules.

        :param search_term: Optional search filter
        :param limit: Maximum number of suggestions
        :return: list of {'value': str, 'display': str} dictionaries
        """
        self.ensure_one()

        if not self.enable_autocomplete:
            return []

        all_values = []
        seen_values = set()

        for rule in self.validation_rule_ids.filtered("active"):
            if rule.validation_type in ("allowed_values", "dynamic_source", "range"):
                values = rule.get_autocomplete_values(search_term, limit)
                for v in values:
                    if v["value"] not in seen_values:
                        all_values.append(v)
                        seen_values.add(v["value"])
                        if len(all_values) >= limit:
                            break
            if len(all_values) >= limit:
                break

        return all_values

    def get_cascade_effects(self, value, attribute_set_id=None):
        """
        Get cascade effects when this attribute's value changes.

        :param value: The new value
        :param attribute_set_id: Optional attribute set context
        :return: list of effect dictionaries
        """
        self.ensure_one()
        return self.env[
            "attribute.validation.cascade"
        ].get_cascade_effects_for_attribute(self.id, value, attribute_set_id)

    def action_view_validation_rules(self):
        """View validation rules for this attribute."""
        self.ensure_one()
        return {
            "name": "Validation Rules",
            "type": "ir.actions.act_window",
            "res_model": "attribute.validation.rule",
            "view_mode": "list,form",
            "domain": [("id", "in", self.validation_rule_ids.ids)],
            "context": {
                "default_attribute_ids": [(4, self.id)],
            },
        }
