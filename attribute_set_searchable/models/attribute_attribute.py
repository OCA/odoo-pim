# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    searchable = fields.Boolean(default=False)

    def _get_custom_filter(self):
        self.ensure_one()
        return self.env["ir.ui.custom.field.filter"].search(
            [("attribute_id", "=", self.id)]
        )

    def _prepare_create_custom_filter(self):
        self.ensure_one()
        model_id = self.attribute_group_id.model_id
        return {
            "model_id": model_id.id,
            "name": self.field_description,
            "expression": self.name,
            "sequence": self.sequence,
            "attribute_id": self.id,
        }

    def _create_custom_filter(self):
        data = self._prepare_create_custom_filter()
        return self.env["ir.ui.custom.field.filter"].create(data)

    def _update_custom_filter(self, custom_filter):
        self.ensure_one()
        data = {}
        if custom_filter.name != self.field_description:
            data.update({"name": self.field_description})
        if custom_filter.expression != self.name:
            data.update({"expression": self.name})
        if custom_filter.sequence != self.sequence:
            data.update({"sequence": self.sequence})
        if data:
            custom_filter.write(data)

    def write(self, vals):
        res = super().write(vals)
        for attribute in self:
            custom_filter = attribute._get_custom_filter()
            if attribute.searchable:
                if not custom_filter:
                    attribute._create_custom_filter()
                else:
                    attribute._update_custom_filter(custom_filter)
            elif custom_filter:
                custom_filter.unlink()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        attributes = super().create(vals_list)
        search_attributes = attributes.filtered("searchable")
        for attribute in search_attributes:
            attribute._create_custom_filter()
        return attributes
