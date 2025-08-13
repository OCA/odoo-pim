odoo.define("product_creation_dynamic_wizard.kanban_button", function (require) {
    "use strict";
    var KanbanController = require("web.KanbanController");
    KanbanController.include({
        events: _.extend({}, KanbanController.prototype.events, {
            "click .o-kanban-button-new-wizard": "_onProductCreationWizardOpen",
        }),
        _onProductCreationWizardOpen: function () {
            this.do_action(
                "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
            );
        },
    });
});
