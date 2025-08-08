odoo.define("product_creation_dynamic_wizard.form_button", function (require) {
    "use strict";
    var FormController = require("web.FormController");
    var FormView = require("web.FormView");
    var viewRegistry = require("web.view_registry");
    var FormButton = FormController.extend({
        buttons_template: "product_creation_dynamic_wizard.buttons.form",
        // RenderButtons: function ($node) {
        //  this._super.apply(this, arguments);
        //  if (this.$buttons) {
        //    this.$buttons.on(
        //      "click",
        //      ".o_form_button_create_wizard",
        //      this._OpenWizardForm.bind(this)
        //    );
        //  }
        // },
        events: _.extend({}, FormController.prototype.events, {
            "click .o_form_button_create_wizard": "_onProductCreationWizardOpen",
        }),
        _onProductCreationWizardOpen: function () {
            this.do_action(
                "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
            );
        },
    });
    var ExtendedFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: FormButton,
        }),
    });
    viewRegistry.add("product_creation_dynamic_wizard_form", ExtendedFormView);
});
