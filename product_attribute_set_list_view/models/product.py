# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


class ProductAttributeListMixin(models.AbstractModel):
    """Inject attribute fields as optional columns on list views."""

    _name = "product.attribute.list.mixin"
    _description = "Product attribute list view mixin"

    @api.model
    def _get_attribute_list_columns(self):
        return self.env["attribute.attribute"].search(
            [
                ("model", "=", self._name),
                ("attribute_set_ids", "!=", False),
                ("nature", "=", "custom"),
            ]
        )

    @api.model
    def _inject_attribute_columns_in_list(self, arch):
        eview = etree.fromstring(arch)
        list_node = eview if eview.tag == "list" else eview.find(".//list")
        if list_node is None:
            return arch
        if list_node.get("multi_edit") in (None, ""):
            list_node.set("multi_edit", "1")
        attributes = self._get_attribute_list_columns().sudo()
        existing_field_names = {f.get("name") for f in list_node.xpath("./field")}
        for attr in attributes:
            if attr.name in existing_field_names:
                continue
            kwargs = {
                "name": attr.name,
                "optional": "hide",
                "string": attr.field_description or attr.name,
            }
            if attr.widget:
                kwargs["widget"] = attr.widget
            etree.SubElement(list_node, "field", **kwargs)
        return etree.tostring(eview, pretty_print=True)

    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == "list":
            arch = result.get("arch")
            if arch:
                result["arch"] = self._inject_attribute_columns_in_list(arch)
        return result

    @api.model
    def _get_view_fields(self, view_type, view_models):
        view_models = super()._get_view_fields(view_type, view_models)
        if self._name in view_models and view_type == "list":
            attributes = self._get_attribute_list_columns()
            view_models[self._name].update(attributes.sudo().mapped("name"))
        return view_models


class ProductTemplate(models.Model):
    _inherit = ["product.template", "product.attribute.list.mixin"]
    _name = "product.template"


class ProductProduct(models.Model):
    _inherit = ["product.product", "product.attribute.list.mixin"]
    _name = "product.product"
