# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeSetOwnerMixin(models.AbstractModel):
    """Mixin for consumers of attribute sets."""

    _name = "attribute.set.owner.mixin"
    _description = "Attribute set owner mixin"

    attribute_set_id = fields.Many2one("attribute.set", "Attribute Set")

    @api.model
    def _build_attribute_eview(self):
        """Override Attribute's method _build_attribute_eview() to build an
        attribute eview with the mixin model's attributes"""
        domain = [
            ("model_id.model", "=", self._name),
            ("attribute_set_ids", "!=", False),
        ]
        if not self._context.get("include_native_attribute"):
            domain.append(("nature", "=", "custom"))

        attributes = self.env["attribute.attribute"].search(domain)
        return attributes._build_attribute_eview()

    @api.model
    def remove_native_fields(self, eview):
        """Remove native fields related to native attributes from eview"""
        native_attrs = self.env["attribute.attribute"].search(
            [
                ("model_id.model", "=", self._name),
                ("attribute_set_ids", "!=", False),
                ("nature", "=", "native"),
            ]
        )
        for attr in native_attrs:
            efield = eview.xpath("//field[@name='{}']".format(attr.name))
            if len(efield):
                efield[0].getparent().remove(efield[0])

    def _insert_attribute(self, arch):
        """Replace attributes' placeholders with real fields in form view arch."""
        eview = etree.fromstring(arch)
        form_name = eview.get("string")
        placeholder = eview.xpath("//separator[@name='attributes_placeholder']")

        if len(placeholder) != 1:
            raise ValidationError(
                _(
                    """It is impossible to add Attributes on "%(name)s" xml
                    view as there is
                    not one "<separator name="attributes_placeholder" />" in it.
                    """,
                    name=form_name,
                )
            )

        if self._context.get("include_native_attribute"):
            self.remove_native_fields(eview)
        attribute_eview = self._build_attribute_eview()

        # Insert the Attributes view
        placeholder[0].getparent().replace(placeholder[0], attribute_eview)
        return etree.tostring(eview, pretty_print=True)

    @api.model
    def get_views(self, views, options=None):
        result = super().get_views(views, options=options)
        form_arch = result.get("views", {}).get("form", {}).get("arch")
        if form_arch:
            result["views"]["form"]["arch"] = self._insert_attribute(
                result["views"]["form"]["arch"]
            )
        return result
