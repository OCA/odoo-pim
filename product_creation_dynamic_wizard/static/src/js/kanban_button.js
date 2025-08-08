odoo.define("product_creation_dynamic_wizard.kanban_button", function (require) {
    "use strict";
    var KanbanController = require("web.KanbanController");
    var KanbanView = require("web.KanbanView");
    var viewRegistry = require("web.view_registry");
    var KanbanButton = KanbanController.extend({
        buttons_template: "product_creation_dynamic_wizard.buttons.kanban",
        events: _.extend({}, KanbanController.prototype.events, {
            "click .o-kanban-button-new-wizard": "_onProductCreationWizardOpen",
        }),
        _onProductCreationWizardOpen: function () {
            this.do_action(
                "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
            );
        },
    });
    var ExtendedKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: KanbanButton,
        }),
    });
    viewRegistry.add("product_creation_dynamic_wizard_kanban", ExtendedKanbanView);
});
