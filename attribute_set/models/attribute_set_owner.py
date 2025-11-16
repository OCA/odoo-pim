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

    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        domain=lambda self: self._get_attribute_set_owner_model(),
    )

    @api.model
    def _get_attribute_set_owner_model(self):
        return [("model", "=", self._name)]

    @api.model
    def _build_attribute_eview(self):
        """Override Attribute's method _build_attribute_eview() to build an
        attribute eview with the mixin model's attributes"""
        domain = [
            ("model", "=", self._name),
            ("attribute_set_ids", "!=", False),
        ]
        if not self.env.context.get("include_native_attribute_view_ref"):
            domain.append(("nature", "=", "custom"))

        attributes = self.env["attribute.attribute"].search(domain)
        return attributes._build_attribute_eview()

    @api.model
    def remove_native_fields(self, eview):
        """Remove native fields related to native attributes from eview"""
        native_attrs = self.env["attribute.attribute"].search(
            [
                ("model", "=", self._name),
                ("attribute_set_ids", "!=", False),
                ("nature", "=", "native"),
            ]
        )
        for attr in native_attrs:
            efield = eview.xpath(f"//field[@name='{attr.name}']")
            if len(efield):
                efield[0].getparent().remove(efield[0])

    def _insert_attribute(self, arch):
        """Replace attributes' placeholders with real fields in form view arch."""
        # Use a context to prevent recursive insertion
        if self.env.context.get("attribute_insertion_in_progress"):
            return arch  # Already in the middle of insertion, return as is

        # Create a new environment with the flag set to prevent recursive calls
        self_with_context = self.with_context(attribute_insertion_in_progress=True)

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

        if self.env.context.get("include_native_attribute_view_ref"):
            # Use the context-aware self for the native fields removal too
            self_with_context.remove_native_fields(eview)
        attribute_eview = self_with_context._build_attribute_eview()

        # Insert the Attributes view
        placeholder[0].getparent().replace(placeholder[0], attribute_eview)

        # Convert back to string
        result_arch = etree.tostring(eview, pretty_print=True)
        return result_arch

    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == "form":
            form_arch = result.get("arch")
            if form_arch:
                # to prevent recursive or duplicate insertion
                if not self.env.context.get("attribute_insertion_in_progress"):
                    # Prevent processing on all res.partner calls by checking conditions
                    result["arch"] = self._insert_attribute(result["arch"])
        return result

    @api.model
    def _get_view_fields(self, view_type, models):
        models = super()._get_view_fields(view_type, models)
        if self._name in models and view_type == "form":
            # we must ensure that the fields defined in the attributes set
            # are declared into the list of fields to load for the form view
            domain = [
                ("model", "=", self._name),
                ("attribute_set_ids", "!=", False),
            ]
            attributes = self.env["attribute.attribute"].search(domain)
            models[self._name].update(attributes.sudo().mapped("name"))
        return models


# For basic functionality in Odoo 19, add the attribute_set_id field to res.partner
# This allows the test view creation to work without the full mixin functionality
class ResPartner(models.Model):
    _inherit = "res.partner"

    # Add the attribute_set_id field to res.partner for basic functionality
    attribute_set_id = fields.Many2one(
        "attribute.set",
        "Attribute Set",
        domain=lambda self: self.env[
            "attribute.set.owner.mixin"
        ]._get_attribute_set_owner_model(),
    )
