odoo.define(
    "product_creation_dynamic_wizard.tree_button_create_wizard",
    function (require) {
        "use strict";
        var ListController = require("web.ListController");
        ListController.include({
            events: _.extend({}, ListController.prototype.events, {
                "click .o_list_button_add_wizard": "_onProductCreationWizardOpen",
            }),
            _onProductCreationWizardOpen: function () {
                this.do_action(
                    "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
                );
            },
        });
    }
);
