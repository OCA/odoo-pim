# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import ormcache


class AttributeSetOwnerMixin(models.AbstractModel):
    """Mixin for consumers of attribute sets."""

    _inherit = "attribute.set.owner.mixin"

    @api.model
    @ormcache("model_name", "attribute_set_id", "include_native")
    def _get_ecom_visible_attribute_ids(
        self, model_name, attribute_set_id, include_native
    ):
        """Cached lookup of e-commerce visible attribute IDs for an attribute set.

        This avoids repeated database queries when displaying multiple products
        with the same attribute set on the shop page.
        """
        domain = [
            ("model", "=", model_name),
            ("attribute_set_ids", "in", [attribute_set_id]),
            ("e_com_visibility", "=", True),
        ]
        if not include_native:
            domain.append(("nature", "=", "custom"))
        return self.env["attribute.attribute"].search(domain).ids

    def get_extra_attributes(self):
        """Get extra product's attribute for e-commerce website."""
        self.ensure_one()
        if not self.attribute_set_id:
            return self.env["attribute.attribute"]

        include_native = self.env.context.get(
            "include_native_attribute_view_ref", False
        )
        attr_ids = self._get_ecom_visible_attribute_ids(
            self._name, self.attribute_set_id.id, include_native
        )
        return self.env["attribute.attribute"].browse(attr_ids)
