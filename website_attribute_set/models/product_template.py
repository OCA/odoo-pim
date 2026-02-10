# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import OrderedDict

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_extra_attribute_values(self, extra_attribute=None):
        self.ensure_one()
        if extra_attribute:
            attr_type = extra_attribute.attribute_type or extra_attribute.ttype
            name = (
                f"{extra_attribute.name}_filename"
                if attr_type in ("binary", "image")
                else extra_attribute.name
            )
            return self[name] if self[name] else None
        return None

    def _prepare_simple_additional_attributes_for_display(self):
        """The returned groups are ordered following their default order.

        The returned groups are ordered following their default order.

        :return: OrderedDict [{
            attribute.group: OrderedDict [{
                attribute.attribute: [values]
            }]
        }]
        """
        attributes = self.get_extra_attributes()
        groups = OrderedDict(
            [(group, OrderedDict()) for group in attributes.attribute_group_id.sorted()]
        )
        for attribute in attributes.filtered(lambda a: a.e_com_specification):
            values = self.get_extra_attribute_values(attribute)
            if isinstance(values, models.BaseModel):
                if len(values) == 1:
                    groups[attribute.attribute_group_id][attribute] = [values.name]
                elif len(values) > 1:
                    groups[attribute.attribute_group_id][attribute] = values.mapped(
                        "name"
                    )
            elif values:
                groups[attribute.attribute_group_id][attribute] = values
        groups = OrderedDict(
            [
                (group, attributes)
                for (group, attributes) in groups.items()
                if attributes
            ]
        )
        return groups
