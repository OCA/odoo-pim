# Copyright 2020 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttributeSetOwnerMixin(models.AbstractModel):
    """Override the '_inheriting' model's fields_view_get() and replace
    the 'attributes_placeholder' by the fields related to the '_inheriting' model's
    Attributes.
    Each Attribute's field will have a conditional invisibility depending on its
    Attribute Sets.
    """

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
            domain.append(("attribute_nature", "=", "custom"))

        attributes = self.env["attribute.attribute"].search(domain)
        return attributes._build_attribute_eview()

    @api.model
    def remove_native_fields(self, eview):
        """Remove native fields related to native attributes from eview"""
        native_attrs = self.env["attribute.attribute"].search(
            [
                ("model_id.model", "=", self._name),
                ("attribute_set_ids", "!=", False),
                ("attribute_nature", "=", "native"),
            ]
        )
        for attr in native_attrs:
            efield = eview.xpath("//field[@name='{}']".format(attr.name))[0]
            efield.getparent().remove(efield)

    def _insert_attribute(self, arch):
        """Insert the model's Attributes related fields into the arch's view form
        at the placeholder's place."""
        eview = etree.fromstring(arch)
        form_name = eview.get("string")
        placeholder = eview.xpath("//separator[@name='attributes_placeholder']")

        if len(placeholder) != 1:
            raise ValidationError(
                _(
                    """It is impossible to add Attributes on "{}" xml view as there is
                    not one "<separator name="attributes_placeholder" />" in it.
                    """.format(
                        form_name
                    )
                )
            )

        if self._context.get("include_native_attribute"):
            self.remove_native_fields(eview)
        attribute_eview = self._build_attribute_eview()

        # Insert the Attributes view
        placeholder[0].getparent().replace(placeholder[0], attribute_eview)
        return etree.tostring(eview, pretty_print=True)

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super(AttributeSetOwnerMixin, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu,
        )
        if view_type == "form":
            result["arch"] = self._insert_attribute(result["arch"])
        return result
