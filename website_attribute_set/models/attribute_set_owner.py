# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AttributeSetOwnerMixin(models.AbstractModel):
    """Mixin for consumers of attribute sets."""

    _inherit = "attribute.set.owner.mixin"

    def get_extra_attributes(self):
        """Get extra product's attribute for e-commerce website.

        Walks the attribute set hierarchy so that a product assigned to a
        child set also exposes the attributes inherited from any ancestor
        set, matching the behaviour of the backend form view.
        """
        self.ensure_one()
        domain = [
            ("model", "=", self._name),
            ("attribute_set_ids", "!=", False),
        ]
        attribute = self.env["attribute.attribute"]
        if self.attribute_set_id:
            attributes = attribute.search(domain)
            attribute_set_id = self.attribute_set_id
            filtered_attributes = attributes.filtered(
                lambda rec: attribute_set_id.id in rec._get_all_set_ids()
                and rec.e_com_visibility
            )
            return filtered_attributes
        else:
            return attribute
