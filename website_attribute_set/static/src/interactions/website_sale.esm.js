import {WebsiteSale} from "@website_sale/interactions/website_sale";
import {patch} from "@web/core/utils/patch";
import {redirect} from "@web/core/utils/urls";
import wSaleUtils from "@website_sale/js/website_sale_utils";

patch(WebsiteSale.prototype, {
    /**
     * @param {Event} ev
     */
    onChangeAttribute(ev) {
        const productGrid = this.el.querySelector(
            ".o_wsale_products_grid_table_wrapper"
        );
        if (productGrid) {
            productGrid.classList.add("opacity-50");
        }
        const form = wSaleUtils.getClosestProductForm(ev.currentTarget);
        const filters = form.querySelectorAll("input:checked, select");
        const rangeInputs = form.querySelectorAll("input[type='number']");
        const additional_attributeValues = new Map();
        const attributeValues = new Map();
        const rangeFilters = new Map();
        const tags = new Set();
        for (const filter of filters) {
            if (filter.value) {
                if (filter.name === "additional_attribute_value") {
                    // Group attribute value ids by attribute id.
                    const firstDash = filter.value.indexOf("-");
                    const [attributeId, attributeValueId] = [
                        filter.value.slice(0, firstDash),
                        filter.value.slice(firstDash + 1),
                    ];
                    const valueIds =
                        additional_attributeValues.get(attributeId) ?? new Set();
                    valueIds.add(attributeValueId);
                    additional_attributeValues.set(attributeId, valueIds);
                } else if (filter.name === "attribute_value") {
                    // Group attribute value ids by attribute id.
                    const [attributeId, attributeValueId] = filter.value.split("-");
                    const valueIds = attributeValues.get(attributeId) ?? new Set();
                    valueIds.add(attributeValueId);
                    attributeValues.set(attributeId, valueIds);
                } else if (filter.name === "tags") {
                    tags.add(filter.value);
                } else {
                    return super.onChangeAttribute(...arguments);
                }
            }
        }
        // Collect range filter inputs (additional_attr_min_ID / additional_attr_max_ID).
        for (const input of rangeInputs) {
            if (input.value) {
                rangeFilters.set(input.name, input.value);
            }
        }
        const url = new URL(form.action);
        const searchParams = url.searchParams;
        // Aggregate all attribute values belonging to the same attribute into a single
        // `additional_attribute_values` search param.
        for (const entry of additional_attributeValues.entries()) {
            searchParams.append(
                "additional_attribute_values",
                `${entry[0]}-${[...entry[1]].join(",")}`
            );
        }
        // Aggregate all attribute values belonging to the same attribute into a single
        // `attribute_values` search param.
        for (const entry of attributeValues.entries()) {
            searchParams.append(
                "attribute_values",
                `${entry[0]}-${[...entry[1]].join(",")}`
            );
        }
        // Append range filter params (additional_attr_min_ID / additional_attr_max_ID).
        for (const [name, value] of rangeFilters.entries()) {
            searchParams.set(name, value);
        }
        // Aggregate all tags into a single `tags` search param.
        if (tags.size) {
            searchParams.set("tags", [...tags].join(","));
        }
        redirect(`${url.pathname}?${searchParams.toString()}`);
    },
});
