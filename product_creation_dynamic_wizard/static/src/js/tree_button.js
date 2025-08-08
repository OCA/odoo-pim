odoo.define("product_creation_dynamic_wizard.tree_button_create_wizard", function (
    require
) {
    "use strict";
    var ListController = require("web.ListController");
    var ListView = require("web.ListView");
    var viewRegistry = require("web.view_registry");
    var TreeButton = ListController.extend({
        buttons_template: "product_creation_dynamic_wizard.buttons.tree",
        events: _.extend({}, ListController.prototype.events, {
            "click .o_list_button_add_wizard": "_onProductCreationWizardOpen",
        }),
        _onProductCreationWizardOpen: function () {
            this.do_action(
                "product_creation_dynamic_wizard.product_creation_dynamic_wizard_action"
            );
        },
    });
    var ExtendedListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });
    viewRegistry.add("product_creation_dynamic_wizard_tree", ExtendedListView);
});
