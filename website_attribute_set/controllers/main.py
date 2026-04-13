# Copyright 2025 Kencove (http://www.kencove.com).
# @author Mohamed Alkobrosli <malkobrosly@kencove.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import itertools
from datetime import datetime

from odoo import fields
from odoo.fields import Domain
from odoo.http import request, route
from odoo.models import BaseModel
from odoo.tools import SQL, float_round, lazy

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.const import SHOP_PATH
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.models.website import PRICELIST_SESSION_CACHE_KEY


class WebsiteSale(main.WebsiteSale):
    @route()
    def shop(  # noqa: C901
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        tags="",
        **post,
    ):
        if not request.website.has_ecommerce_access():
            return request.redirect(f"/web/login?redirect={request.httprequest.path}")

        is_category_in_query = category and isinstance(category, str)
        category = self._validate_and_get_category(category)
        # If the category is provided as a query parameter (which is deprecated),
        # we redirect to the "correct" shop URL, where the category has been
        # removed from the query parameters and added to the path.
        if is_category_in_query:
            query = self._get_filtered_query_string(
                request.httprequest.query_string.decode(), keys_to_remove=["category"]
            )
            return request.redirect(
                f"{self._get_shop_path(category, page)}?{query}", code=301
            )

        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        website = request.env["website"].get_current_website()
        website_domain = website.website_domain()

        ppg = website.shop_ppg or 21
        ppr = website.shop_ppr or 4
        gap = website.shop_gap or "16px"

        request_args = request.httprequest.args
        attribute_values = request_args.getlist("attribute_values")
        attribute_value_dict = self._get_attribute_value_dict(attribute_values)
        attribute_ids = set(attribute_value_dict.keys())
        attribute_value_ids = set(
            itertools.chain.from_iterable(attribute_value_dict.values())
        )
        if attribute_values:
            request.session["attribute_values"] = attribute_values
        else:
            request.session.pop("attribute_values", None)

        # START HOOK 1
        additional_attribute_values = request_args.getlist(
            "additional_attribute_values"
        )
        additional_attribute_values = self._get_additional_attribute_value_list(
            additional_attribute_values
        )
        additional_attribute_set = set(tuple(x) for x in additional_attribute_values)
        if additional_attribute_values:
            request.session["additional_attribute_values"] = additional_attribute_values
            post["additional_attribute_values"] = additional_attribute_values
            post["additional_attribute_set"] = additional_attribute_set
        else:
            request.session.pop("additional_attribute_values", None)

        # Parse range filter parameters (for numeric attributes)
        additional_range_filters = {}
        for key in request_args.keys():
            if key.startswith("additional_attr_min_"):
                attr_id = int(key.replace("additional_attr_min_", ""))
                additional_range_filters.setdefault(attr_id, {})
                try:
                    additional_range_filters[attr_id]["min"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue
            elif key.startswith("additional_attr_max_"):
                attr_id = int(key.replace("additional_attr_max_", ""))
                additional_range_filters.setdefault(attr_id, {})
                try:
                    additional_range_filters[attr_id]["max"] = float(request_args[key])
                except (ValueError, TypeError):
                    continue
        if additional_range_filters:
            request.session["additional_range_filters"] = additional_range_filters
            post["additional_range_filters"] = additional_range_filters
        else:
            request.session.pop("additional_range_filters", None)
        # END HOOK 1

        filter_by_tags_enabled = website.is_view_active(
            "website_sale.filter_products_tags"
        )
        if filter_by_tags_enabled:
            if tags:
                post["tags"] = tags
                tags = {self.env["ir.http"]._unslug(tag)[1] for tag in tags.split(",")}
            else:
                post["tags"] = None
                tags = {}

        url = self._get_shop_path(category)
        keep = QueryURL(
            url, **self._shop_get_query_url_kwargs(search, min_price, max_price, **post)
        )

        # Check if we need to refresh the cached pricelist
        now = datetime.timestamp(datetime.now())
        if "website_sale_pricelist_time" in request.session:
            pricelist_save_time = request.session["website_sale_pricelist_time"]
            if pricelist_save_time < now - 60 * 60:
                request.session.pop(PRICELIST_SESSION_CACHE_KEY, None)
                # restart the counter
                request.session["website_sale_pricelist_time"] = now

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

        if search:
            post["search"] = search

        options = self._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
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
            # TODO Find an alternative way to obtain
            # the domain through the search metadata.
            Product = request.env["product.template"].with_context(bin_size=True)
            search_term = fuzzy_search_term if fuzzy_search_term else search
            domain = self._get_shop_domain(search_term, category, attribute_value_dict)

            # This is ~4 times more efficient than a search
            # for the cheapest and most expensive products
            query = Product._search(domain)
            sql = query.select(
                SQL(
                    "COALESCE(MIN(list_price), 0) * %(conversion_rate)s, "
                    "COALESCE(MAX(list_price), 0) * %(conversion_rate)s",
                    conversion_rate=conversion_rate,
                )
            )
            available_min_price, available_max_price = request.env.execute_query(sql)[0]

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
            all_tags = ProductTag.search_fetch(
                Domain.AND(
                    [
                        Domain("visible_to_customers", "=", True),
                        Domain.OR(
                            [
                                Domain("product_template_ids.is_published", "=", True),
                                Domain("product_ids.is_published", "=", True),
                            ]
                        ),
                        website_domain,
                    ]
                )
            )
        else:
            all_tags = ProductTag

        # categories

        Category = request.env["product.public.category"]
        categs_domain = Domain("parent_id", "=", False) & website_domain
        if not self.env.user._is_internal():
            categs_domain &= Domain("has_published_products", "=", True)
        if search:
            search_categories = Category.search(
                Domain("product_tmpl_ids", "in", search_product.ids) & website_domain
            ).parents_and_self
            categs_domain &= Domain("id", "in", search_categories.ids)
        else:
            search_categories = Category
        categs = Category.search_fetch(categs_domain)

        category_entries = Category
        if category:
            category_entries = (
                not search
                and category.child_id
                or category.child_id.filtered(lambda c: c.id in search_categories.ids)
            )
            if not category_entries:
                parent = category.parent_id
                category_entries = (
                    not search
                    and parent.child_id
                    or parent.child_id.filtered(lambda c: c.id in search_categories.ids)
                )
        else:
            category_entries = categs
        if not request.env.user._is_internal():
            category_entries = category_entries.filtered("has_published_products")

        # products for current pager

        pager = website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post
        )
        offset = pager["offset"]
        products = search_product[offset : offset + ppg]
        products.fetch()

        # map each product to its variant, and prefetch the variants
        variants = (
            request.env["product.product"]
            .sudo()
            .browse(product._get_first_possible_variant_id() for product in products)
        )
        variants.fetch()
        product_variants = dict(zip(products, variants, strict=False))

        ProductAttribute = request.env["product.attribute"]
        if products:
            # get all products without limit
            attributes_grouped = request.env[
                "product.template.attribute.line"
            ]._read_group(
                domain=[
                    ("product_tmpl_id", "in", search_product.ids),
                    ("attribute_id.visibility", "=", "visible"),
                ],
                groupby=["attribute_id"],
                order="attribute_id",
            )
            attribute_ids = [attribute.id for (attribute,) in attributes_grouped]
            attributes = ProductAttribute.browse(attribute_ids)
        else:
            attributes = ProductAttribute.browse(attribute_ids).sorted()

        if website.is_view_active("website_sale.products_list_view"):
            layout_mode = "list"
        else:
            layout_mode = "grid"

        products_prices = products._get_sales_prices(website)
        product_query_params = self._get_product_query_params(**post)

        grouped_attributes_values = (
            request.env["product.attribute.value"]
            .browse(attribute_value_ids)
            .sorted()
            .grouped("attribute_id")
        )

        values = {
            "auto_assign_ribbons": self.env["product.ribbon"]
            .sudo()
            .search([("assign", "!=", "manual")]),
            "search": fuzzy_search_term or search,
            "original_search": fuzzy_search_term and search,
            "order": post.get("order", ""),
            "category": category,
            "attrib_values": attribute_value_dict,
            "attrib_set": attribute_value_ids,
            # START HOOK 2
            "additional_attrib_set": additional_attribute_set,
            # END HOOK 2
            "pager": pager,
            "products": products,
            "product_variants": product_variants,
            "search_product": search_product,
            "search_count": product_count,  # common for all searchbox
            "bins": main.TableCompute().process(products, ppg, ppr),
            "ppg": ppg,
            "ppr": ppr,
            "gap": gap,
            "categories": categs,
            "category_entries": category_entries,
            "attributes": attributes,
            "keep": keep,
            "search_categories_ids": search_categories.ids,
            "layout_mode": layout_mode,
            "get_product_prices": lambda product: products_prices[product.id],
            "float_round": float_round,
            "shop_path": SHOP_PATH,
            "product_query_params": product_query_params,
            "grouped_attributes_values": grouped_attributes_values,
            "previewed_attribute_values": lazy(
                lambda: products._get_previewed_attribute_values(
                    category, product_query_params
                ),
            ),
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
        values.update(self._get_additional_shop_values(values, **post))
        return request.render("website_sale.products", values)

    @staticmethod
    def _get_additional_attribute_value_list(attribute_values):
        """Parses a list of attribute value query params, and returns a list
        grouping attribute values by attribute id.

        :param list(str) attribute_values: The list of attribute value
        query parameters to parse.
        :return: A list grouping attribute values by attribute id.
        :rtype: list([int, list(int)])
        """
        attribute_value_pairs = [
            value.split("-", maxsplit=1)
            for value in attribute_values
            if value and value[0] != "["
        ]
        return [[int(pair[0]), pair[1]] for pair in attribute_value_pairs]

    def _get_search_options(
        self,
        category=None,
        attribute_value_dict=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        values = super()._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        if post.get("additional_attribute_values", False):
            values["additional_attribute_values"] = post["additional_attribute_values"]
        return values

    def _get_additional_shop_values(self, values, **kwargs):
        # Can be used to search & filter products depending on their custom attributes
        """Hook to update values used for rendering website_sale.products template"""
        extra_values = super()._get_additional_shop_values(values, **kwargs)
        extra_values.update(
            {
                "additional_attributes": [],
            }
        )
        if values.get("products"):
            search_product = values.get("search_product")
            all_additional_attributes = request.env["attribute.attribute"].sudo()
            product_attrs_map = {}
            # loop to get all attributes that only haves values
            # that can be displayed in e-commerce website
            for product in search_product:
                additional_attributes = product.sudo().get_extra_attributes()
                if additional_attributes:
                    product_attrs_map[product.id] = additional_attributes
                    all_additional_attributes |= additional_attributes

            if all_additional_attributes:
                # loop to get all assigned attribute values for all related products
                for attribute in all_additional_attributes:
                    all_attribute_values = set()
                    value_counts = {}

                    for product in search_product:
                        if attribute not in product_attrs_map.get(product.id, []):
                            continue
                        attribute_values = product.sudo().get_extra_attribute_values(
                            attribute
                        )
                        if attribute_values:
                            # To avoid repetition of select options in the template
                            # We make sure if the attribute_values is a single value or
                            # if it is a recordset we loop through it
                            if (
                                isinstance(attribute_values, BaseModel)
                                and len(attribute_values) > 1
                            ):
                                for rec in attribute_values:
                                    all_attribute_values.add(rec)
                                    if attribute.e_com_show_count:
                                        key = rec.id if hasattr(rec, "id") else rec
                                        value_counts[key] = value_counts.get(key, 0) + 1
                            else:
                                all_attribute_values.add(attribute_values)
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

    def _prepare_product_values(self, product, category, **kwargs):
        vals = super()._prepare_product_values(product, category, **kwargs)

        last_attributes_search = request.session.get("attribute_values", [])
        last_additional_attributes_search = request.session.get(
            "additional_attribute_values", []
        )
        if last_attributes_search and last_additional_attributes_search:
            keep = QueryURL(
                self._get_shop_path(category),
                attribute_values=last_attributes_search,
                additional_attribute_values=last_additional_attributes_search,
            )
            vals["keep"] = keep
        elif last_additional_attributes_search:
            keep = QueryURL(
                self._get_shop_path(category),
                additional_attribute_values=last_additional_attributes_search,
            )
            vals["keep"] = keep

        additional_attributes = product.sudo().get_extra_attributes()
        if additional_attributes:
            vals.update({"additional_attributes": []})
            for attribute in additional_attributes:
                attribute_values = product.sudo().get_extra_attribute_values(attribute)
                vals["additional_attributes"].append(
                    {"attribute": attribute, "attribute_values": attribute_values}
                )
        return vals

    def _shop_get_query_url_kwargs(
        self, search, min_price, max_price, order=None, tags=None, **kwargs
    ):
        res = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, order, tags, **kwargs
        )
        additional_attribute_values = request.session.get(
            "additional_attribute_values", []
        )
        res["additional_attribute_values"] = additional_attribute_values
        return res

    def _get_shop_domain(self, search, category, attribute_value_dict, **kwargs):
        """Extend shop domain with additional attribute filters."""
        domain = super()._get_shop_domain(
            search, category, attribute_value_dict, **kwargs
        )

        additional_attribute_values = request.session.get(
            "additional_attribute_values", []
        )
        additional_range_filters = request.session.get("additional_range_filters", {})

        additional_conditions = []
        additional_conditions.extend(
            self._build_range_filter_conditions(additional_range_filters)
        )
        additional_conditions.extend(
            self._build_value_filter_conditions(additional_attribute_values)
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
                conditions.append(Domain(field_name, ">=", range_vals["min"]))
            if "max" in range_vals:
                conditions.append(Domain(field_name, "<=", range_vals["max"]))
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
            return Domain(field_name, "=", value)
        elif attr_type in ("select", "multiselect"):
            try:
                option_id = int(attr_value)
                return Domain(field_name, "=", option_id)
            except (ValueError, TypeError):
                return None
        elif attr_type == "integer":
            try:
                return Domain(field_name, "=", int(attr_value))
            except (ValueError, TypeError):
                return None
        elif attr_type == "float":
            try:
                return Domain(field_name, "=", float(attr_value))
            except (ValueError, TypeError):
                return None
        else:
            # char, text, date, datetime - use exact match
            return Domain(field_name, "=", attr_value)
