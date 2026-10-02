"""Attribute Validation Rule model for data validation without Many2one relations."""

import json
import logging
import re

from odoo import api, fields, models
from odoo.tools.safe_eval import datetime as safe_datetime
from odoo.tools.safe_eval import safe_eval, wrap_module

_logger = logging.getLogger(__name__)

_SAFE_RE = wrap_module(
    re,
    [
        "match",
        "search",
        "fullmatch",
        "sub",
        "findall",
        "split",
        "compile",
        "escape",
        "IGNORECASE",
        "MULTILINE",
        "DOTALL",
    ],
)


class AttributeValidationRule(models.Model):
    """Define validation rules for attribute values."""

    _name = "attribute.validation.rule"
    _description = "Attribute Validation Rule"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(help="Technical identifier for programmatic access")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # === Rule Type ===
    validation_type = fields.Selection(
        selection=[
            ("regex", "Regular Expression"),
            ("allowed_values", "Allowed Values List"),
            ("dynamic_source", "Dynamic Source (Model)"),
            ("range", "Numeric Range"),
            ("python", "Python Expression"),
        ],
        required=True,
        default="allowed_values",
    )

    # === Regex Validation ===
    regex_pattern = fields.Char(
        help="Python regex pattern. Example: ^[A-Z]{2}[0-9]{4}$"
    )
    regex_flags = fields.Selection(
        selection=[
            ("none", "None"),
            ("ignorecase", "Case Insensitive"),
            ("multiline", "Multiline"),
        ],
        default="none",
    )

    # === Allowed Values ===
    allowed_value_ids = fields.One2many(
        comodel_name="attribute.validation.allowed.value",
        inverse_name="rule_id",
        string="Allowed Values",
    )

    # === Dynamic Source ===
    source_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Source Model",
        help="Model to fetch allowed values from",
    )
    source_field = fields.Char(
        help="Field to use as value (e.g., 'code', 'name')",
        default="name",
    )
    source_display_field = fields.Char(
        help="Field to display in autocomplete (default: same as source_field)",
    )
    source_domain = fields.Char(
        help="Domain to filter source records. Example: [('active', '=', True)]",
        default="[]",
    )
    source_order = fields.Char(
        help="Order clause for source records",
        default="name",
    )
    cache_timeout = fields.Integer(
        string="Cache Timeout (seconds)",
        default=3600,
        help="How long to cache dynamic source values. 0 = no cache.",
    )

    # === Range Validation ===
    range_min = fields.Float(string="Minimum Value")
    range_max = fields.Float(string="Maximum Value")
    range_min_inclusive = fields.Boolean(default=True)
    range_max_inclusive = fields.Boolean(default=True)
    range_step = fields.Float(
        help="Allowed increment (e.g., 0.5 for half values). 0 = any.",
    )

    # === Python Expression ===
    python_code = fields.Text(
        help="""Python expression that returns True if valid.
Available variables:
- value: The value being validated
- record: The record being validated (if available)
- env: Odoo environment
- datetime, date, time: datetime modules
- re: regex module

Example: value.isdigit() and int(value) % 2 == 0
""",
    )

    # === Error Handling ===
    error_message = fields.Char(
        translate=True,
        help="Custom error message. Use {value} placeholder.",
    )

    # === Metadata ===
    attribute_ids = fields.Many2many(
        comodel_name="attribute.attribute",
        relation="attribute_validation_rule_rel",
        column1="rule_id",
        column2="attribute_id",
        string="Used By Attributes",
    )
    usage_count = fields.Integer(
        compute="_compute_usage_count",
        string="# Attributes",
    )

    @api.depends("attribute_ids")
    def _compute_usage_count(self):
        for rule in self:
            rule.usage_count = len(rule.attribute_ids)

    def validate(self, value, record=None):
        """
        Validate a value against this rule.

        :param value: The value to validate
        :param record: Optional record context for python expressions
        :return: tuple (is_valid: bool, error_message: str or None)
        """
        self.ensure_one()

        # Empty values are skipped (handled by the required constraint);
        # 0 / 0.0 are real values and must still be validated.
        if value is None or value is False or value == "":
            return True, None

        method = getattr(self, f"_validate_{self.validation_type}", None)
        if not method:
            return True, None

        return method(value, record)

    def _validate_regex(self, value, record=None):
        """Validate value against regex pattern."""
        if not self.regex_pattern:
            return True, None

        flags = 0
        if self.regex_flags == "ignorecase":
            flags = re.IGNORECASE
        elif self.regex_flags == "multiline":
            flags = re.MULTILINE

        pattern = re.compile(self.regex_pattern, flags)
        if pattern.fullmatch(str(value)):
            return True, None

        error = self.error_message or f"Value '{value}' does not match pattern"
        return False, error.format(value=value)

    def _validate_allowed_values(self, value, record=None):
        """Validate value against static allowed values list."""
        allowed = self.allowed_value_ids.filtered("active").mapped("value")
        if str(value) in allowed:
            return True, None

        error = self.error_message or f"'{value}' is not in allowed values"
        return False, error.format(value=value)

    def _validate_dynamic_source(self, value, record=None):
        """Validate value against dynamically fetched values from a model."""
        allowed = self._get_dynamic_values()
        if str(value) in allowed:
            return True, None

        model_name = self.source_model_id.name if self.source_model_id else "source"
        error = self.error_message or f"'{value}' not found in {model_name}"
        return False, error.format(value=value)

    def _validate_range(self, value, record=None):
        """Validate value against numeric range."""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, f"'{value}' is not a valid number"

        min_ok = (
            num_value >= self.range_min
            if self.range_min_inclusive
            else num_value > self.range_min
        )
        max_ok = (
            num_value <= self.range_max
            if self.range_max_inclusive
            else num_value < self.range_max
        )

        if not min_ok or not max_ok:
            error = (
                self.error_message
                or f"Value must be between {self.range_min} and {self.range_max}"
            )
            return False, error.format(value=value)

        if self.range_step and self.range_step > 0:
            # Distance to the nearest grid point, measured symmetrically. The
            # old ``% range_step > 0.0001`` test was one-sided: floating-point
            # rounding can push the modulo of a perfectly valid multiple to just
            # *below* the step (step - epsilon) instead of near zero, so a value
            # like 0.3 with step 0.1 (0.3 % 0.1 == 0.0999…) was wrongly rejected.
            steps = (num_value - self.range_min) / self.range_step
            if abs(steps - round(steps)) > 1e-6:
                error = f"Value must be in increments of {self.range_step}"
                return False, error

        return True, None

    def _validate_python(self, value, record=None):
        """Validate value using Python expression."""
        local_vars = {
            "value": value,
            "record": record,
            "env": self.env,
            "datetime": safe_datetime,
            "date": safe_datetime.date,
            "time": safe_datetime.time,
            "re": _SAFE_RE,
        }

        try:
            result = safe_eval(self.python_code, local_vars, mode="eval")
            if result:
                return True, None
            error = self.error_message or f"Validation failed for '{value}'"
            return False, error.format(value=value)
        except Exception as e:
            _logger.warning("Validation error for rule %s: %s", self.name, e)
            return False, f"Validation error: {e}"

    def _get_dynamic_values_cache_key(self):
        """Get cache key for dynamic values."""
        return f"attribute_validation_dynamic_{self.id}"

    def _get_dynamic_values(self):
        """Get allowed values from dynamic source model with caching."""
        self.ensure_one()

        if not self.source_model_id:
            return []

        # Check cache
        cache_key = self._get_dynamic_values_cache_key()
        if self.cache_timeout > 0:
            cached = self.env["ir.config_parameter"].sudo().get_param(cache_key)
            if cached:
                try:
                    cache_data = json.loads(cached)
                    if cache_data.get("expires", 0) > fields.Datetime.now().timestamp():
                        return cache_data.get("values", [])
                except (json.JSONDecodeError, KeyError):
                    _logger.debug(
                        "Ignoring invalid cached dynamic values for %s", cache_key
                    )

        # Fetch from source model
        model = self.env[self.source_model_id.model]
        domain = safe_eval(self.source_domain or "[]")
        records = model.search(domain, order=self.source_order or "id")

        field_name = self.source_field or "name"
        values = [
            str(getattr(r, field_name, ""))
            for r in records
            if getattr(r, field_name, None)
        ]

        # Update cache
        if self.cache_timeout > 0:
            cache_data = {
                "values": values,
                "expires": fields.Datetime.now().timestamp() + self.cache_timeout,
            }
            self.env["ir.config_parameter"].sudo().set_param(
                cache_key, json.dumps(cache_data)
            )

        return values

    def get_autocomplete_values(self, search_term="", limit=50):
        """Get values for autocomplete widget."""
        self.ensure_one()

        if self.validation_type == "allowed_values":
            values = self.allowed_value_ids.filtered(
                lambda v: (
                    v.active
                    and (not search_term or search_term.lower() in v.value.lower())
                )
            )[:limit]
            return [
                {"value": v.value, "display": v.display_value or v.value}
                for v in values
            ]

        elif self.validation_type == "dynamic_source":
            all_values = self._get_dynamic_values()
            if search_term:
                all_values = [v for v in all_values if search_term.lower() in v.lower()]

            # Get display values if different field
            if (
                self.source_display_field
                and self.source_display_field != self.source_field
            ):
                model = self.env[self.source_model_id.model]
                domain = safe_eval(self.source_domain or "[]")
                if search_term:
                    domain.append((self.source_field, "ilike", search_term))
                records = model.search(
                    domain, limit=limit, order=self.source_order or "id"
                )
                return [
                    {
                        "value": str(getattr(r, self.source_field, "")),
                        "display": str(getattr(r, self.source_display_field, "")),
                    }
                    for r in records
                ]

            return [{"value": v, "display": v} for v in all_values[:limit]]

        elif self.validation_type == "range":
            # For ranges with step, provide some common values
            if self.range_step and self.range_step > 0:
                values = []
                current = self.range_min
                while current <= self.range_max and len(values) < limit:
                    str_val = str(int(current) if current == int(current) else current)
                    if not search_term or search_term in str_val:
                        values.append({"value": str_val, "display": str_val})
                    current += self.range_step
                return values

        return []

    def validate_batch(self, values_list):
        """
        Validate multiple values efficiently.

        :param values_list: list of values to validate
        :return: dict mapping value -> (is_valid, error_message)
        """
        self.ensure_one()

        # Pre-fetch dynamic values once for efficiency
        if self.validation_type == "dynamic_source":
            allowed = set(self._get_dynamic_values())
            results = {}
            for value in values_list:
                if str(value) in allowed:
                    results[value] = (True, None)
                else:
                    error = self.error_message or f"'{value}' not found"
                    results[value] = (False, error.format(value=value))
            return results

        # Fall back to individual validation for other types
        return {v: self.validate(v) for v in values_list}

    def action_view_attributes(self):
        """View attributes using this rule."""
        self.ensure_one()
        return {
            "name": "Attributes",
            "type": "ir.actions.act_window",
            "res_model": "attribute.attribute",
            "view_mode": "list,form",
            "domain": [("id", "in", self.attribute_ids.ids)],
        }

    def action_clear_cache(self):
        """Clear the dynamic values cache for this rule."""
        self.ensure_one()
        if self.validation_type == "dynamic_source":
            cache_key = self._get_dynamic_values_cache_key()
            self.env["ir.config_parameter"].sudo().set_param(cache_key, False)
        return True
