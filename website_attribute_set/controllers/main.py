# Copyright 2011 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
