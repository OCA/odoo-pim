/** @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import {registry} from "@web/core/registry";
import {listView} from "@web/views/list/list_view";
export class ProductVectorCharacteristicsListController extends ListController {
    setup() {
        super.setup();
    }
    OnClickVectorizationWizard() {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "product.field.vectorization.wizard",
                name: "Vectorize field",
                views: [[false, "form"]],
                target: "new",
            },
            {
                // Ensures the new created records are loaded once we close the wizard
                onClose: () => {
                    this.model.load();
                },
            }
        );
    }
}

registry.category("views").add("vectorization_wizard_button_in_tree", {
    ...listView,
    Controller: ProductVectorCharacteristicsListController,
    buttonTemplate: "product_vector_characteristic.ListView.Buttons",
});
