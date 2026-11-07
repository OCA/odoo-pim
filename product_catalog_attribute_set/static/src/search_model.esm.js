/** @odoo-module **/

/**  Copyright 2025 Kencove (http://www.kencove.com).
     @author Mohamed Alkobrosli <malkobrosly@kencove.com>
     License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). **/

import {Domain} from "@web/core/domain";
import {SearchModel} from "@web/search/search_model";
import {patch} from "@web/core/utils/patch";

/**
 * The patch is to override sending a value to limit parameter.
 * The default value for limit parameter is None and we prefer it.
 **/
patch(SearchModel.prototype, {
    async _fetchFilters(filters) {
        const evalContext = {};
        for (const category of this.categories) {
            evalContext[category.fieldName] = category.activeValueId;
        }
        const categoryDomain = this._getCategoryDomain();
        const searchDomain = this.searchDomain;
        await Promise.all(
            filters.map(async (filter) => {
                const result = await this.orm.call(
                    this.resModel,
                    "search_panel_select_multi_range",
                    [filter.fieldName],
                    {
                        category_domain: categoryDomain,
                        comodel_domain: new Domain(filter.domain).toList(evalContext),
                        context: this.globalContext,
                        enable_counters: filter.enableCounters,
                        filter_domain: this._getFilterDomain(filter.id),
                        expand: filter.expand,
                        group_by: filter.groupBy || false,
                        group_domain: this._getGroupDomain(filter),
                        search_domain: searchDomain,
                    }
                );
                this._createFilterTree(filter.id, result);
            })
        );
    },
});
