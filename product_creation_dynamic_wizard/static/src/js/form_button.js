odoo.define("product_creation_dynamic_wizard.form_button", function (require) {
    "use strict";
    var FormController = require("web.FormController");
    FormController.include({
        events: _.extend({}, FormController.prototype.events, {
            "click .o_form_button_create_wizard": "_onProductCreationWizardOpen",
        }),
        _onProductCreationWizardOpen: function () {
            this.do_action(
                "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
            );
        },
    });
});
