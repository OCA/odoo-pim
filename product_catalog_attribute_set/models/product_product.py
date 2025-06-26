# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from collections import Counter

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _get_extra_attributes(self):
        """Override Attribute's method _build_attribute_eview() to build an
        attribute eview with the mixin model's attributes"""
        domain = [
            ("attribute_set_ids", "!=", False),
            ("model", "=", "product.template"),
            ("nature", "=", "custom"),
        ]
        attributes = self.env["attribute.attribute"].sudo().search(domain)
        return attributes

    def _create_filter_attributes(self, attributes, parent, index):
        for attribute in attributes:
            if attribute.ttype == "many2many":
                field_node = etree.Element(
                    "field",
                    name=attribute.name,
                    icon="fa-th-list",
                    enable_counters="1",
                    select="multi",
                )
                parent.insert(index + 1, field_node)
                index += 1
            elif attribute.ttype in ("many2one"):
                field_node = etree.Element(
                    "field",
                    name=attribute.name,
                    icon="fa-th-list",
                )
                parent.insert(index + 1, field_node)
                index += 1
        return parent

    def _create_search_attributes(self, attributes, parent, index):
        for attribute in attributes:
            field_node = etree.Element(
                "field",
                name=attribute.name,
            )
            parent.insert(index + 1, field_node)
            index += 1
        return parent

    def _insert_extra_search_attribute(self, arch, separator, is_filter=False):
        """Replace attributes' placeholders with real fields in form view arch."""
        eview = etree.fromstring(arch)
        form_name = eview.get("string")
        placeholder = eview.xpath(f"//separator[@name='{separator}']")
        if len(placeholder) != 1:
            raise ValidationError(
                _(
                    """It is impossible to add Attributes on "%(name)s" xml
                    view as there is
                    not one "<separator name="%(separator)s" />" in it.
                    """,
                    name=form_name,
                    separator=separator,
                )
            )
        attributes = self._get_extra_attributes()
        parent = placeholder[0].getparent()
        index = parent.index(placeholder[0])
        if is_filter:
            parent = self._create_filter_attributes(attributes, parent, index)
        else:
            parent = self._create_search_attributes(attributes, parent, index)
        # Remove the placeholder
        parent.remove(placeholder[0])
        return etree.tostring(eview, pretty_print=True)

    def get_view(self, view_id=None, view_type="search", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == "search":
            form_arch = result.get("arch")
            if form_arch:
                # Add attributes in filter sidebar
                result["arch"] = self._insert_extra_search_attribute(
                    result["arch"],
                    separator="attributes_filter_placeholder",
                    is_filter=True,
                )
                # Add attributes in search panel
                result["arch"] = self._insert_extra_search_attribute(
                    result["arch"], separator="attributes_search_placeholder"
                )
        return result

    def extra_attr_vals(self, all_products, attr):
        """
        Return a list of each attribute value or a list of
        lists having id, value if value of type attribute.option
        """
        count = 0
        vals_list = []
        for product in all_products:
            if product[attr.name]:
                count += 1
                product_tmpl_id = product.product_tmpl_id
                val = product_tmpl_id.get_extra_attribute_values(attr)
                if val:
                    if isinstance(val, models.BaseModel) and len(val) >= 1:
                        for v in val:
                            vals_list.append(v.name)
                    else:
                        vals_list.append(val)
        counter = Counter(vals_list)
        # Convert to list of [value, count]
        result = [[val, count] for val, count in counter.items()]
        return result, count

    def catalog_extra_attrs(self):
        product = self.env["product.product"].sudo()
        all_attrs = self._get_extra_attributes()
        filtered_attrs = all_attrs.filtered(
            lambda r: r.ttype not in ["many2many", "many2one"]
        )
        all_products = product.search([])
        attrs_data = []
        for attr in filtered_attrs:
            vals, count = self.extra_attr_vals(all_products, attr)
            attr_data = {
                "id": attr.id,
                "name": attr.name,
                "display_name": attr.field_description,
                "count": count,
            }
            if vals:
                attr_data["vals"] = vals
            attrs_data.append(attr_data)
        return attrs_data
