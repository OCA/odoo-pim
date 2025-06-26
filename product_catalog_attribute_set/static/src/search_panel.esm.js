/** @odoo-module **/

/**  Copyright 2025 Kencove (http://www.kencove.com).
     @author Mohamed Alkobrosli <malkobrosly@kencove.com>
     License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). **/

import {registry} from "@web/core/registry";
import {ProductCatalogSearchPanel} from "@product/product_catalog/search/search_panel";
import {productCatalogKanbanView} from "@product/product_catalog/kanban_view";
import {useService} from "@web/core/utils/hooks";
import {onWillStart, useState} from "@odoo/owl";
import {productCatalogStore} from "./kanban_model.esm";

export class ProductCatalogSearchPanel2 extends ProductCatalogSearchPanel {
    static template = "web.SearchPanel.Custom";
    static subTemplates = {
        ...ProductCatalogSearchPanel.subTemplates,
    };
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            ...this.state,
            extra_attrs: [],
            productCatalogStore,
            isDomainInSearch: (x, y, z) => this.checkIfDomainInSearch(x, y, z),
        });
        onWillStart(async () => {
            await this.loadExtraAttrs();
        });
    }

    checkIfDomainInSearch(facets, attr, value) {
        const domain = this.getDomain(attr, value);
        const facet = facets.find((q) => q.domain === domain);
        if (facet) return true;
        return false;
    }

    async loadExtraAttrs() {
        const ids = this.state.productCatalogStore.visibleIds;
        if (this.state.productCatalogStore?.visibleIds?.length) {
            this.state.extra_attrs = await this.orm.call(
                "product.product",
                "catalog_extra_attrs",
                [ids],
                {}
            );
            this.updateActiveValues();
        }
    }

    getDomain(attr, value = null) {
        let domain = "";
        if (value !== null) {
            domain = `[("${attr.name}", "ilike", "${value}")]`;
        } else {
            domain = `[("${attr.name}", "!=", None)]`;
        }
        return domain;
    }

    async toggleSectionFilterValue2(attr, value = null, ev = {}) {
        const domain = this.getDomain(attr, value);
        if (ev.currentTarget.checked) {
            const preFilter = {
                description: domain,
                domain: domain,
                invisible: "True",
                type: "filter",
            };
            this.env.searchModel.createNewFilters([preFilter]);
        } else {
            const facets = this.env.searchModel.facets;
            const facet = facets.find((q) => q.domain === domain);
            if (facet) {
                this.env.searchModel.deactivateGroup(facet.groupId);
            }
        }
    }
}

registry.category("views").remove("product_kanban_catalog");
registry.category("views").add("product_kanban_catalog", {
    ...productCatalogKanbanView,
    SearchPanel: ProductCatalogSearchPanel2,
});
