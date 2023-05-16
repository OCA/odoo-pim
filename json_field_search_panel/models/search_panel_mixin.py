from odoo import api, models
from odoo.osv.expression import AND, expression


class SearchPanelMixin(models.AbstractModel):
    _inherit = "search.panel.mixin"
    _json_attributes_set_name = "json_attributes_set"

    @api.model
    def _search_panel_json(self, field_name, kwargs, attribute):
        # since we aren't using Odoo methods to search, we need to check
        # user permissions manually
        self.check_access_rights("read")

        attribute_set_ids = (
            self.env["attribute.set"]
            .search([("attribute_ids", "in", (attribute.id,))])
            .ids
        )
        if attribute_set_ids:
            kwargs["search_domain"] = AND(
                [
                    kwargs.get("search_domain", []),
                    [("attribute_set_id", "in", attribute_set_ids)],
                ]
            )

        domain = self._build_doamin_search_panel(kwargs)

        query = expression(domain, self).query

        # When we use select on a query object, we can define the select clause
        query_sql = query.select(f"DISTINCT {self._json_attributes_set_name} ->%s")

        params = [field_name] + query_sql[1]

        self._apply_ir_rules(query, "read")

        self.env.cr.execute(query_sql[0], params=params)
        result = self.env.cr.fetchall()

        if attribute.attribute_type == "boolean":
            # Cast to bool so null becomes false
            distinct_values = [bool(value[0]) for value in result]
        else:
            distinct_values = [value[0] for value in result]

        selection = self._get_selection(self._fields[field_name], field_name)

        return {
            "parent_field": False,
            "values": self._define_panel_values_labels(
                distinct_values, selection, self._fields[field_name]
            ),
        }

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        attribute = self.env["attribute.attribute"].search([("name", "=", field_name)])
        if attribute and attribute.nature == "json_postgresql":
            return self._search_panel_json(field_name, kwargs, attribute)

        return super().search_panel_select_range(field_name, **kwargs)
