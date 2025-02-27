# Copyright 2011 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    def shop(
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        rendered_templ = super().shop(
            page, category, search, min_price, max_price, ppg, **post
        )
        return rendered_templ

    def _get_additional_shop_values(self, values):
        # Can be used to search & filter products depending on their custom attributes
        """Hook to update values used for rendering website_sale.products template"""
        extra_values = super()._get_additional_shop_values(values)
        extra_values.update(
            {
                "additional_attributes": [],
            }
        )
        products = values.get("products")
        all_additional_attributes = request.env["attribute.attribute"].sudo()
        if products:
            # loop to get all attributes that only haves values
            # that can be displayed in e-commerce website
            for product in products:
                additional_attributes = product.sudo().get_extra_attributes()
                if additional_attributes:
                    all_additional_attributes |= additional_attributes

            if all_additional_attributes:
                # loop to get all assigned attribute values for all related products
                for attribute in all_additional_attributes:
                    all_attribute_values = set()
                    for product in products:
                        attribute_values = product.sudo().get_extra_attribute_values(
                            attribute
                        )
                        if attribute_values:
                            all_attribute_values.add(attribute_values)
                    extra_values["additional_attributes"].append(
                        {
                            "attribute": attribute,
                            "all_attribute_values": list(all_attribute_values),
                        }
                    )
        # anyalyze the url args to be used in filter and search
        request_args = request.httprequest.args
        additional_attrib_list = request_args.getlist("additional_attribute_value")
        additional_attrib_values = [
            [x for x in v.split("-", maxsplit=1)] for v in additional_attrib_list if v
        ]
        additional_attrib_values = [
            [int(sublist[0]), sublist[1]] for sublist in additional_attrib_values
        ]
        additional_attrib_set = set(
            (item[0], item[1]) for item in additional_attrib_values
        )
        values["additional_attrib_set"] = additional_attrib_set
        return extra_values

    def product(self, product, category="", search="", **kwargs):
        rendered_templ = super().product(product, category, search, **kwargs)
        return rendered_templ

    def _prepare_product_values(self, product, category, search, **kwargs):
        # If the product has a value for attribute_set_id
        # this will pass the attributes related to it's attribute_set_id
        # and then to be rendered in the website
        vals = super()._prepare_product_values(product, category, search, **kwargs)
        additional_attributes = product.sudo().get_extra_attributes()
        if additional_attributes:
            vals.update({"additional_attributes": []})
            for attribute in additional_attributes:
                attribute_values = product.sudo().get_extra_attribute_values(attribute)
                vals["additional_attributes"].append(
                    {"attribute": attribute, "attribute_values": attribute_values}
                )
        return vals
