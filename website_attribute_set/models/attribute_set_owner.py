# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


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
        if not self.attribute_set_id:
            return self.env["attribute.attribute"]
        return self._get_extra_attributes_per_set(self.attribute_set_id.ids).get(
            self.attribute_set_id.id, self.env["attribute.attribute"]
        )

    @api.model
    def _get_extra_attributes_per_set(self, attribute_set_ids):
        """Return ``{attribute_set_id: attributes_recordset}`` for given sets.

        Batched counterpart of :meth:`get_extra_attributes`: resolves each
        attribute's descendant attribute sets only once instead of once per
        owner record, which removes the quadratic ``child_of`` search cost
        when the method is used over a listing (e.g. the shop page).
        """
        attribute = self.env["attribute.attribute"]
        if not attribute_set_ids:
            return {}
        attributes = attribute.search(
            [
                ("model", "=", self._name),
                ("attribute_set_ids", "!=", False),
                ("e_com_visibility", "=", True),
            ]
        )
        attr_descendants = {
            attr.id: set(attr._get_all_set_ids()) for attr in attributes
        }
        result = {}
        for set_id in set(attribute_set_ids):
            result[set_id] = attributes.filtered(
                lambda a, sid=set_id: sid in attr_descendants[a.id]
            )
        return result
