# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import OrderedDict

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_additional_attributes_for_display(self):
        """The returned groups are ordered following their default order.

        :return: OrderedDict [{
            attribute.group: OrderedDict [{
                attribute.attribute: OrderedDict [{
                    product.product: value
                }]
            }]
        }]
        """
        attributes = self.env["attribute.attribute"]
        for product in self:
            attributes |= product.product_tmpl_id.get_extra_attributes()
        groups = OrderedDict(
            [(group, OrderedDict()) for group in attributes.attribute_group_id.sorted()]
        )
        for attribute in attributes:
            groups[attribute.attribute_group_id][attribute] = OrderedDict(
                [
                    (
                        product,
                        product.product_tmpl_id.get_extra_attribute_values(attribute),
                    )
                    for product in self
                ]
            )
            for product in groups[attribute.attribute_group_id][attribute]:
                values = groups[attribute.attribute_group_id][attribute][product]
                if isinstance(values, models.BaseModel):
                    if len(values) == 1:
                        groups[attribute.attribute_group_id][attribute][product] = (
                            values.name
                        )
                    elif len(values) > 1:
                        groups[attribute.attribute_group_id][attribute][product] = (
                            values.mapped("name")
                        )
        return groups
