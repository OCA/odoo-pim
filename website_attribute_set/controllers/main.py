# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from werkzeug.exceptions import NotFound

from odoo import fields
from odoo.fields import Domain
from odoo.http import request, route
from odoo.models import BaseModel
from odoo.tools import float_round, groupby, lazy

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    @route()
    def shop(  # noqa: C901
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        if not request.website.has_ecommerce_access():
            return request.redirect("/web/login")
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        Category = request.env["product.public.category"]
        if category:
            category = Category.search([("id", "=", int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        website = request.env["website"].get_current_website()
        website_domain = website.website_domain()
        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        gap = website.shop_gap or "16px"

        request_args = request.httprequest.args
        attrib_list = request_args.getlist("attribute_value")
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        if attrib_list:
            post["attribute_value"] = attrib_list

        # analyze the url args to be used in filter and search
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
        post["additional_attrib_set"] = additional_attrib_set
        post["additional_attrib_values"] = additional_attrib_values

        # Parse range filter parameters (for numeric attributes)
        additional_range_filters = {}
        for key in request_args.keys():
            if key.startswith("additional_attr_min_"):
                attr_id = int(key.replace("additional_attr_min_", ""))
                if attr_id not in additional_range_filters:
                    additional_range_filters[attr_id] = {}
                try:
                    additional_range_filters[attr_id]["min"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue  # Skip invalid numeric values
            elif key.startswith("additional_attr_max_"):
                attr_id = int(key.replace("additional_attr_max_", ""))
                if attr_id not in additional_range_filters:
                    additional_range_filters[attr_id] = {}
                try:
                    additional_range_filters[attr_id]["max"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue  # Skip invalid numeric values
        post["additional_range_filters"] = additional_range_filters

        filter_by_tags_enabled = website.is_view_active(
            "website_sale.filter_products_tags"
        )
        if filter_by_tags_enabled:
            tags = request_args.getlist("tags")
            # Allow only numeric tag values to avoid internal error.
            if tags and all(tag.isnumeric() for tag in tags):
                post["tags"] = tags
                tags = {int(tag) for tag in tags}
            else:
                post["tags"] = None
                tags = {}

        keep = QueryURL(
            "/shop",
            **self._shop_get_query_url_kwargs(
                category and int(category), search, min_price, max_price, **post
            ),
        )

        now = datetime.timestamp(datetime.now())
        # In Odoo 19, pricelist is accessed through user context, not website
        pricelist = request.env.user.property_product_pricelist

        if "website_sale_pricelist_time" in request.session:
            # Check if we need to refresh the cached pricelist
            pricelist_save_time = request.session["website_sale_pricelist_time"]
            if pricelist_save_time < now - 60 * 60:
                request.session.pop("website_sale_current_pl", None)
                # Clear the session cache for pricelist
                new_pricelist = request.env.user.property_product_pricelist
                pricelist = new_pricelist
                request.session["website_sale_pricelist_time"] = now
                request.session["website_sale_current_pl"] = pricelist.id
        else:
            request.session["website_sale_pricelist_time"] = now
            request.session["website_sale_current_pl"] = pricelist.id

        filter_by_price_enabled = website.is_view_active(
            "website_sale.filter_products_price"
        )
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = request.env["res.currency"]._get_conversion_rate(
                company_currency,
                website.currency_id,
                request.website.company_id,
                fields.Date.today(),
            )
        else:
            conversion_rate = 1

        url = "/shop"
        if search:
            post["search"] = search

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            **post,
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
            options, post, search, website
        )

        filter_by_price_enabled = website.is_view_active(
            "website_sale.filter_products_price"
        )
        if filter_by_price_enabled:
            # Get min/max prices for the filter using a standard aggregate approach
            Product = request.env["product.template"].with_context(bin_size=True)
            domain = self._get_shop_domain(
                search,
                category,
                attrib_values,
                additional_attrib_values=post.get("additional_attrib_values"),
            )

            # Use the more robust aggregate method to get min/max prices
            # This is the Odoo 19 compatible approach
            try:
                # Get min and max prices using search and aggregate
                results = Product.search_read(domain, ["list_price"])
                if results:
                    list_prices = [
                        r["list_price"] or 0 for r in results if r.get("list_price")
                    ]
                    if list_prices:
                        available_min_price = min(list_prices)
                        available_max_price = max(list_prices)
                    else:
                        available_min_price = available_max_price = 0
                else:
                    available_min_price = available_max_price = 0
            except (ValueError, TypeError):
                available_min_price = available_max_price = 0

            if min_price or max_price:
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists,
                # the price filter is set to their respective available prices
                # when the specified min exceeds the max, and / or
                # the specified max is lower than the available min.
                if min_price:
                    min_price = (
                        min_price
                        if min_price <= available_max_price
                        else available_min_price
                    )
                    post["min_price"] = min_price
                if max_price:
                    max_price = (
                        max_price
                        if max_price >= available_min_price
                        else available_max_price
                    )
                    post["max_price"] = max_price

        ProductTag = request.env["product.tag"]
        if filter_by_tags_enabled and search_product:
            all_tags = ProductTag.search(
                Domain.AND(
                    [
                        [
                            ("product_ids.is_published", "=", True),
                        ],
                        website_domain,
                    ]
                )
            )
        else:
            all_tags = ProductTag

        categs_domain = [("parent_id", "=", False)] + website_domain
        if search:
            search_categories = Category.search(
                [("product_tmpl_ids", "in", search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(("id", "in", search_categories.ids))
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))

        if category:
            url = "/shop/category/{}".format(request.env["ir.http"]._slug(category))

        pager = website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post
        )
        offset = pager["offset"]
        products = search_product[offset : offset + ppg]

        # Compute product variants (required by Odoo 19 templates)
        variants = (
            request.env["product.product"]
            .sudo()
            .browse(product._get_first_possible_variant_id() for product in products)
        )
        variants.fetch()
        product_variants = dict(zip(products, variants, strict=False))

        # Get product query params for attribute previews
        product_query_params = self._get_product_query_params(**post)

        # Category entries for navigation
        if category:
            category_entries = category.child_id
        else:
            category_entries = categs

        ProductAttribute = request.env["product.attribute"]
        if products:
            # get all products without limit
            attributes = lazy(
                lambda: ProductAttribute.search(
                    [
                        ("product_tmpl_ids", "in", search_product.ids),
                        ("visibility", "=", "visible"),
                    ]
                )
            )
        else:
            attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))

        layout_mode = request.session.get("website_sale_shop_layout_mode")
        if not layout_mode:
            if website.viewref("website_sale.products_list_view").active:
                layout_mode = "list"
            else:
                layout_mode = "grid"
            request.session["website_sale_shop_layout_mode"] = layout_mode

        products_prices = products._get_sales_prices(website)

        attributes_values = request.env["product.attribute.value"].browse(attrib_set)
        sorted_attributes_values = attributes_values.sorted("sequence")
        multi_attributes_values = sorted_attributes_values.filtered(
            lambda av: av.display_type == "multi"
        )
        single_attributes_values = sorted_attributes_values - multi_attributes_values
        grouped_attributes_values = list(
            groupby(single_attributes_values, lambda av: av.attribute_id.id)
        )
        grouped_attributes_values.extend(
            [(av.attribute_id.id, [av]) for av in multi_attributes_values]
        )

        selected_attributes_hash = (
            "#attribute_values={}".format(
                ",".join(str(v[0].id) for k, v in grouped_attributes_values)
            )
            if grouped_attributes_values
            else ""
        )

        values = {
            "search": fuzzy_search_term or search,
            "original_search": fuzzy_search_term and search,
            "order": post.get("order", ""),
            "category": category,
            "category_entries": category_entries,
            "attrib_values": attrib_values,
            "attrib_set": attrib_set,
            "additional_attrib_set": additional_attrib_set,
            "pager": pager,
            "products": products,
            "product_variants": product_variants,
            "previewed_attribute_values": lazy(
                lambda: products._get_previewed_attribute_values(
                    category, product_query_params
                )
            ),
            "search_product": search_product,
            "search_count": product_count,  # common for all searchbox
            "bins": main.TableCompute().process(products, ppg, ppr),
            "ppg": ppg,
            "ppr": ppr,
            "gap": gap,
            "categories": categs,
            "attributes": attributes,
            "keep": keep,
            "selected_attributes_hash": selected_attributes_hash,
            "search_categories_ids": search_categories.ids,
            "layout_mode": layout_mode,
            "products_prices": products_prices,
            "get_product_prices": lambda product: products_prices[product.id],
            "float_round": float_round,
        }
        if filter_by_price_enabled:
            values["min_price"] = min_price or available_min_price
            values["max_price"] = max_price or available_max_price
            values["available_min_price"] = float_round(available_min_price, 2)
            values["available_max_price"] = float_round(available_max_price, 2)
        if filter_by_tags_enabled:
            values.update({"all_tags": all_tags, "tags": tags})
        if category:
            values["main_object"] = category
        values.update(self._get_additional_shop_values(values))

        return request.render("website_sale.products", values)

    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        values = super()._get_search_options(
            category=category,
            attrib_values=attrib_values,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        if post.get("additional_attrib_values"):
            values["additional_attrib_values"] = post.get("additional_attrib_values")
        return values

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
        search_product = values.get(
            "search_product"
        )  # All matching products for counts
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
                    value_counts = {}

                    # Use search_product for counting if available, else use products
                    count_products = search_product or products

                    for product in count_products:
                        attribute_values = product.sudo().get_extra_attribute_values(
                            attribute
                        )
                        if attribute_values:
                            # To avoid repeatition of select options in the template
                            # We make sure if the attribute_values is a single value or
                            # if it is a recordset we loop through it
                            if (
                                isinstance(attribute_values, BaseModel)
                                and len(attribute_values) > 1
                            ):
                                for rec in attribute_values:
                                    all_attribute_values.add(rec)
                                    # Count products per value (use id for records)
                                    if attribute.e_com_show_count:
                                        key = rec.id if hasattr(rec, "id") else rec
                                        value_counts[key] = value_counts.get(key, 0) + 1
                            else:
                                all_attribute_values.add(attribute_values)
                                # Count products per value
                                if attribute.e_com_show_count:
                                    if hasattr(attribute_values, "id"):
                                        key = attribute_values.id
                                    else:
                                        key = attribute_values
                                    value_counts[key] = value_counts.get(key, 0) + 1

                    attr_dict = {
                        "attribute": attribute,
                        "all_attribute_values": list(all_attribute_values),
                    }
                    if attribute.e_com_show_count:
                        attr_dict["value_counts"] = value_counts
                    extra_values["additional_attributes"].append(attr_dict)

        return extra_values

    def _get_shop_domain(self, search, category, attrib_values, **post):
        """Extend shop domain with additional attribute filters."""
        additional_attrib_values = post.get("additional_attrib_values", [])
        additional_range_filters = post.get("additional_range_filters", {})

        domain = super()._get_shop_domain(search, category, attrib_values)
        additional_conditions = []

        # Handle range and value filters
        additional_conditions.extend(
            self._build_range_filter_conditions(additional_range_filters)
        )
        additional_conditions.extend(
            self._build_value_filter_conditions(additional_attrib_values)
        )

        if additional_conditions:
            return Domain.AND([domain] + additional_conditions)
        return domain

    def _build_range_filter_conditions(self, range_filters):
        """Build domain conditions for range filters (min/max)."""
        conditions = []
        Attribute = request.env["attribute.attribute"].sudo()
        for attr_id, range_vals in range_filters.items():
            attribute = Attribute.browse(attr_id)
            if not attribute.exists():
                continue
            field_name = attribute.name
            if "min" in range_vals:
                conditions.append((field_name, ">=", range_vals["min"]))
            if "max" in range_vals:
                conditions.append((field_name, "<=", range_vals["max"]))
        return conditions

    def _build_value_filter_conditions(self, attrib_values):
        """Build domain conditions for value filters (select, boolean, etc.)."""
        if not attrib_values:
            return []

        conditions = []
        Attribute = request.env["attribute.attribute"].sudo()

        # Group values by attribute for multi-select support
        attr_values_grouped = {}
        for attr_id, attr_value in attrib_values:
            attr_values_grouped.setdefault(attr_id, []).append(attr_value)

        for attr_id, values in attr_values_grouped.items():
            attribute = Attribute.browse(attr_id)
            if not attribute.exists():
                continue

            field_name = attribute.name
            attr_type = attribute.attribute_type

            # Multi-select: OR within same attribute
            if len(values) > 1 and attribute.e_com_multi_select:
                or_conds = [
                    c
                    for v in values
                    if (c := self._build_attribute_condition(field_name, attr_type, v))
                ]
                if or_conds:
                    conditions.append(Domain.OR(or_conds))
            else:
                for attr_value in values:
                    cond = self._build_attribute_condition(
                        field_name, attr_type, attr_value
                    )
                    if cond:
                        conditions.append(cond)
        return conditions

    def _build_attribute_condition(self, field_name, attr_type, attr_value):
        """Build a single domain condition for an attribute value."""
        if attr_type == "boolean":
            value = attr_value.lower() == "true"
            return [(field_name, "=", value)]
        elif attr_type in ("select", "multiselect"):
            try:
                option_id = int(attr_value)
                return [(field_name, "=", option_id)]
            except (ValueError, TypeError):
                return None
        elif attr_type == "integer":
            try:
                value = int(attr_value)
                return [(field_name, "=", value)]
            except (ValueError, TypeError):
                return None
        elif attr_type == "float":
            try:
                value = float(attr_value)
                return [(field_name, "=", value)]
            except (ValueError, TypeError):
                return None
        else:
            # char, text, date, datetime - use exact match
            return [(field_name, "=", attr_value)]

    def _prepare_product_values(self, product, category, **kwargs):
        # If the product has a value for attribute_set_id
        # this will pass the attributes related to it's attribute_set_id
        # and then to be rendered in the website
        vals = super()._prepare_product_values(product, category, **kwargs)
        # Always set additional_attributes (even if empty) to ensure template
        # variable exists
        vals["additional_attributes"] = []
        extra_attributes = product.sudo().get_extra_attributes()
        for attribute in extra_attributes:
            attribute_values = product.sudo().get_extra_attribute_values(attribute)
            if attribute_values:
                vals["additional_attributes"].append(
                    {"attribute": attribute, "attribute_values": attribute_values}
                )
        return vals
