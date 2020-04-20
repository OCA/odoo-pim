# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AttributeSetOwnerMixin(models.AbstractModel):
    _name = "attribute.set.owner.mixin"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.model
    def _build_attribute_view(self):
        attributes = self.env["attribute.attribute"].search(
            [("model_id.model", "=", self._name), ("attribute_set_ids", "!=", False)]
        )
        return attributes._build_attribute_view()
