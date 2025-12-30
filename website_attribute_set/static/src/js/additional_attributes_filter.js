/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdditionalAttributesFilter = publicWidget.Widget.extend({
    selector: "#wsale_products_attributes_collapse",
    events: {
        "change select[name='additional_attribute_value']":
            "_onAdditionalAttributeChange",
        "change input[name='additional_attribute_value']":
            "_onAdditionalAttributeChange",
    },

    /**
     * Handle change events on additional attribute filter inputs.
     * Submits the form to apply the filter.
     * @param {Event} ev
     */
    _onAdditionalAttributeChange: function (ev) {
        const form = this.el.closest("form");
        if (form) {
            form.submit();
        } else {
            // Fallback: manually update URL with filter parameters
            this._updateUrlWithFilters();
        }
    },

    /**
     * Fallback method to update URL with filter parameters if no form found.
     */
    _updateUrlWithFilters: function () {
        const url = new URL(window.location.href);
        const params = url.searchParams;

        // Remove existing additional_attribute_value params
        params.delete("additional_attribute_value");

        // Add current selections
        const selects = this.el.querySelectorAll(
            "select[name='additional_attribute_value']"
        );
        selects.forEach((select) => {
            if (select.value) {
                params.append("additional_attribute_value", select.value);
            }
        });

        const checkboxes = this.el.querySelectorAll(
            "input[name='additional_attribute_value']:checked"
        );
        checkboxes.forEach((checkbox) => {
            if (checkbox.value) {
                params.append("additional_attribute_value", checkbox.value);
            }
        });

        // Navigate to the new URL
        window.location.href = url.toString();
    },
});

export default publicWidget.registry.AdditionalAttributesFilter;
