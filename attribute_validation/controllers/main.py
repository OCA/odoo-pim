"""HTTP Controllers for attribute validation."""

from odoo import http
from odoo.http import request


class AttributeValidationController(http.Controller):
    """REST endpoints for attribute validation and autocomplete."""

    @http.route("/attribute_validation/autocomplete", type="jsonrpc", auth="user")
    def autocomplete(self, attribute_id, search_term="", limit=10):
        """
        Get autocomplete suggestions for an attribute.

        :param attribute_id: ID of the attribute
        :param search_term: Optional search filter
        :param limit: Maximum number of suggestions
        :return: list of {'value': str, 'display': str} dictionaries
        """
        attribute = request.env["attribute.attribute"].browse(attribute_id)
        if not attribute.exists():
            return []
        return attribute.get_autocomplete_values(search_term, limit)

    @http.route("/attribute_validation/validate", type="jsonrpc", auth="user")
    def validate(self, attribute_id, value, record_id=None, model=None):
        """
        Validate a value against an attribute's rules.

        :param attribute_id: ID of the attribute
        :param value: Value to validate
        :param record_id: Optional record ID for context
        :param model: Optional model name for context
        :return: {'is_valid': bool, 'errors': list of str}
        """
        attribute = request.env["attribute.attribute"].browse(attribute_id)
        if not attribute.exists():
            return {"is_valid": True, "errors": []}

        record = None
        if record_id and model:
            try:
                record = request.env[model].browse(record_id)
                if not record.exists():
                    record = None
            except (KeyError, ValueError):
                record = None

        is_valid, errors = attribute.validate_value(value, record)
        return {"is_valid": is_valid, "errors": errors}

    @http.route("/attribute_validation/cascade", type="jsonrpc", auth="user")
    def get_cascade_effects(self, attribute_id, value, attribute_set_id=None):
        """
        Get cascade effects when a value changes.

        :param attribute_id: ID of the trigger attribute
        :param value: New value
        :param attribute_set_id: Optional attribute set context
        :return: list of effect dictionaries
        """
        attribute = request.env["attribute.attribute"].browse(attribute_id)
        if not attribute.exists():
            return []

        return attribute.get_cascade_effects(value, attribute_set_id)

    @http.route("/attribute_validation/validate_batch", type="jsonrpc", auth="user")
    def validate_batch(self, attribute_id, values):
        """
        Validate multiple values efficiently.

        :param attribute_id: ID of the attribute
        :param values: List of values to validate
        :return: dict mapping value -> {'is_valid': bool, 'error': str or None}
        """
        attribute = request.env["attribute.attribute"].browse(attribute_id)
        if not attribute.exists():
            return {v: {"is_valid": True, "error": None} for v in values}

        results = {}
        for rule in attribute.validation_rule_ids.filtered("active"):
            batch_results = rule.validate_batch(values)
            for value, (is_valid, error) in batch_results.items():
                if value not in results:
                    results[value] = {"is_valid": True, "errors": []}
                if not is_valid:
                    results[value]["is_valid"] = False
                    if error:
                        results[value]["errors"].append(error)

        # Handle values not yet in results (no rules applied)
        for value in values:
            if value not in results:
                results[value] = {"is_valid": True, "errors": []}

        return results
