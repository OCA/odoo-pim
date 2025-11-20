/** @odoo-module */

import {CharField} from "@web/views/fields/char/char_field";
import {registry} from "@web/core/registry";

// 1. Extend the standard CharField to add suggestions
export class WidgetAutocompleteField extends CharField {
    setup() {
        super.setup();

        // Access the 'fields' category of the main registry
        const widgetRegistry = registry.category("fields");

        // Get all keys (widget names) from the registry
        this.suggestions = [...widgetRegistry.keys()];
    }
}

// 2. Register the new widget
// The 'field_widgets' registry category is used to map the string
// in the 'widget' attribute of the XML view to the component class.
registry.category("field_widgets").add("widget_autocomplete", WidgetAutocompleteField);
