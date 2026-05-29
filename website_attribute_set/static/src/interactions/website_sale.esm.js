import {WebsiteSale} from "@website_sale/interactions/website_sale";
import {patch} from "@web/core/utils/patch";
import {redirect} from "@web/core/utils/urls";
import wSaleUtils from "@website_sale/js/website_sale_utils";

// Delay (ms) before applying a numeric range filter. While the user keeps
// adjusting the value (typing or repeatedly clicking the spinner arrows), each
// keystroke/click resets the timer so the listing is only reloaded once they
// stop and the range is fully entered.
const RANGE_FILTER_DEBOUNCE = 900;

function isRangeFilterInput(el) {
    return Boolean(
        el &&
            el.name &&
            (el.name.startsWith("additional_attr_min_") ||
                el.name.startsWith("additional_attr_max_"))
    );
}

patch(WebsiteSale.prototype, {
    setup() {
        super.setup();
        // The base interaction only reacts to `change` on the filter inputs.
        // For the numeric range inputs we also need `input` so that every
        // keystroke (and spinner click) resets the debounce timer: this lets
        // the user finish typing/adjusting *both* bounds before we search,
        // instead of triggering a search as soon as the first bound changes.
        this.dynamicContent = {
            ...this.dynamicContent,
            "form.js_attributes input[type='number']": {
                "t-on-input": this.onChangeAttribute,
            },
        };
    },

    /**
     * @param {Event} ev
     */
    onChangeAttribute(ev) {
        const target = ev.currentTarget;
        // The actual work, kept as an arrow so `super` and `arguments` stay
        // bound to this method even when called from the debounce timeout.
        const apply = () => {
            const productGrid = this.el.querySelector(
                ".o_wsale_products_grid_table_wrapper"
            );
            if (productGrid) {
                productGrid.classList.add("opacity-50");
            }
            const form = wSaleUtils.getClosestProductForm(target);
            const filters = form.querySelectorAll("input:checked, select");
            const rangeInputs = form.querySelectorAll("input[type='number']");
            const additional_attributeValues = new Map();
            const attributeValues = new Map();
            const tags = new Set();
            for (const filter of filters) {
                if (filter.value) {
                    if (filter.name === "additional_attribute_values") {
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
                    } else if (!isRangeFilterInput(filter)) {
                        return super.onChangeAttribute(...arguments);
                    }
                }
            }
            const url = new URL(form.action);
            const searchParams = url.searchParams;
            // Aggregate all attribute values belonging to the same attribute into a
            // single `additional_attribute_values` search param.
            for (const entry of additional_attributeValues.entries()) {
                searchParams.append(
                    "additional_attribute_values",
                    `${entry[0]}-${[...entry[1]].join(",")}`
                );
            }
            // Aggregate all attribute values belonging to the same attribute into a
            // single `attribute_values` search param.
            for (const entry of attributeValues.entries()) {
                searchParams.append(
                    "attribute_values",
                    `${entry[0]}-${[...entry[1]].join(",")}`
                );
            }
            // Apply the numeric range filter inputs
            // (additional_attr_min_ID / additional_attr_max_ID). An empty input
            // removes the param so the bound is actually cleared instead of
            // keeping the previously submitted value. Note: `""` is the only
            // value to treat as empty here -- "0" and negative values are valid
            // bounds and must be kept.
            for (const input of rangeInputs) {
                if (input.value === "") {
                    searchParams.delete(input.name);
                } else {
                    searchParams.set(input.name, input.value);
                }
            }
            // Aggregate all tags into a single `tags` search param.
            if (tags.size) {
                searchParams.set("tags", [...tags].join(","));
            }
            redirect(`${url.pathname}?${searchParams.toString()}`);
        };
        if (isRangeFilterInput(target)) {
            // Debounce: wait until the user stops adjusting the value before
            // searching, instead of reloading the listing on every increment or
            // before the second bound of the range has been entered.
            clearTimeout(this._rangeFilterTimeout);
            this._rangeFilterTimeout = this.waitForTimeout(
                apply,
                RANGE_FILTER_DEBOUNCE
            );
            return;
        }
        return apply();
    },
});
