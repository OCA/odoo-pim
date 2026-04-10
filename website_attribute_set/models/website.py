# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, models


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _search_get_details(self, search_type, order, options):
        additional_attrib_values = options.get("additional_attrib_values")
        values = super()._search_get_details(
            search_type=search_type, order=order, options=options
        )
        if additional_attrib_values:
            for value in values:
                base_domain = value.get("base_domain")
                for additional_attrib in additional_attrib_values:
                    attribute_id = additional_attrib[0]
                    attribute = (
                        self.env["attribute.attribute"].sudo().browse(attribute_id)
                    )
                    if not attribute.exists():
                        continue
                    attribute_field = attribute.name
                    attribute_type = attribute.attribute_type
                    additional_attrib_value = additional_attrib[1]

                    # Handle different attribute types appropriately
                    if additional_attrib_value.startswith("name-"):
                        # Legacy format: name-model.name-id-123
                        pattern = r"name-(.*?)-id-(\d+)"
                        match = re.search(pattern, additional_attrib_value)
                        if match:
                            model_name = match.group(1)
                            model_id = match.group(2)
                            search_rec_value = (
                                self.env[model_name].sudo().browse(int(model_id))
                            )
                            additional_attrib_domain = [
                                (attribute_field, "in", [search_rec_value.id])
                            ]
                            base_domain.append(additional_attrib_domain)
                    elif attribute_type == "boolean":
                        # Boolean values come as "True" or "False" strings
                        bool_value = additional_attrib_value.lower() == "true"
                        additional_attrib_domain = [(attribute_field, "=", bool_value)]
                        base_domain.append(additional_attrib_domain)
                    elif attribute_type in ("select", "multiselect"):
                        # Select values are option IDs (integers)
                        try:
                            option_id = int(additional_attrib_value)
                            additional_attrib_domain = [
                                (attribute_field, "=", option_id)
                            ]
                            base_domain.append(additional_attrib_domain)
                        except (ValueError, TypeError):
                            continue
                    elif attribute_type == "integer":
                        try:
                            int_value = int(additional_attrib_value)
                            additional_attrib_domain = [
                                (attribute_field, "=", int_value)
                            ]
                            base_domain.append(additional_attrib_domain)
                        except (ValueError, TypeError):
                            continue
                    elif attribute_type == "float":
                        try:
                            float_value = float(additional_attrib_value)
                            additional_attrib_domain = [
                                (attribute_field, "=", float_value)
                            ]
                            base_domain.append(additional_attrib_domain)
                        except (ValueError, TypeError):
                            continue
                    else:
                        # char, text, date, datetime - use exact match
                        additional_attrib_domain = [
                            (attribute_field, "=", additional_attrib_value)
                        ]
                        base_domain.append(additional_attrib_domain)
        return values
