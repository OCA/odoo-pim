/** @odoo-module **/

/**  Copyright 2025 Kencove (http://www.kencove.com).
     @author Mohamed Alkobrosli <malkobrosly@kencove.com>
     License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). **/

import {ProductCatalogKanbanModel} from "@product/product_catalog/kanban_model";
import {patch} from "@web/core/utils/patch";
import {reactive} from "@odoo/owl";

export const productCatalogStore = reactive({
    currentProducts: [],
    visibleIds: [],

    updateIds(data) {
        this.currentProducts = data.records;
        this.visibleIds = this.currentProducts.map((r) => r.id);
        return this.visibleIds;
    },
});

patch(ProductCatalogKanbanModel.prototype, {
    // eslint-disable-next-line no-unused-vars
    async _loadData(params) {
        const result = await super._loadData(...arguments);
        if (result?.records?.length) {
            productCatalogStore.updateIds(result);
        }
        return result;
    },
});
