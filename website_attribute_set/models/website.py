# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, models

from .mixins import _sparse_filter_by_value


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _search_get_details(self, search_type, order, options):
        additional_attrib_values = options.get("additional_attribute_values")
        values = super()._search_get_details(
            search_type=search_type, order=order, options=options
        )
        if additional_attrib_values and not isinstance(additional_attrib_values, str):
            for value in values:
                base_domain = value.get("base_domain")
                for additional_attrib in additional_attrib_values:
                    attribute_id = additional_attrib[0]
                    attribute_field = (
                        self.env["attribute.attribute"].sudo().browse(attribute_id)
                    )
                    attribute_name = attribute_field.name
                    if attribute_field.attribute_type in ("binary", "image"):
                        attribute_name = f"{attribute_name}_filename"
                    additional_attrib_value = additional_attrib[1]

                    # Sparse (serialized) fields cannot be used in ORM domain
                    # conditions because they are not stored in their own SQL
                    # column.  Resolve to a set of matching IDs via a raw JSONB
                    # query so the base_domain stays SQL-safe.
                    pt_field = self.env["product.template"]._fields.get(attribute_name)
                    sparse_col = getattr(pt_field, "sparse", None) if pt_field else None
                    if sparse_col:
                        ids = _sparse_filter_by_value(
                            self.env,
                            "product.template",
                            sparse_col,
                            attribute_name,
                            attribute_field.attribute_type,
                            additional_attrib_value,
                        )
                        if ids:
                            base_domain.append([("id", "in", ids)])
                        continue

                    if attribute_field.attribute_type in (
                        "select",
                        "multiselect",
                    ) or attribute_field.ttype in ("many2one", "many2many"):
                        pattern = r"name-(.*?)-id-(\d+)"
                        match = re.search(pattern, additional_attrib_value)
                        if match:
                            model_name = match.group(1)
                            model_id = match.group(2)
                            search_rec_value = (
                                self.env[model_name].sudo().browse(int(model_id))
                            )
                            additional_attrib_domain = [
                                (attribute_name, "in", [search_rec_value.id]),
                                (
                                    "attribute_set_id",
                                    "in",
                                    attribute_field.attribute_set_ids.ids,
                                ),
                            ]
                            base_domain.append(additional_attrib_domain)
                    else:
                        additional_attrib_domain = [
                            (attribute_name, "=", additional_attrib_value)
                        ]
                        base_domain.append(additional_attrib_domain)
        return values
