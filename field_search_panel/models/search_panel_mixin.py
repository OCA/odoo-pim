from lxml import etree

from odoo import _, api, models
from odoo.osv.expression import AND


class SearchpanelMixin(models.AbstractModel):
    _name = "search.panel.mixin"
    _description = "Mixin Search Panel"

    @api.model
    def get_views(self, views, options=None):
        result = super().get_views(views, options=options)
        if (
            "views" in result
            and "search" in result["views"]
            and "arch" in result["views"]["search"]
        ):
            result["views"]["search"]["arch"] = self._set_dynamic_search_panel(
                result["views"]["search"]["arch"]
            )
        return result

    @api.model
    def _set_dynamic_search_panel(self, arch):

        search_panel_field_ids = self.env[
            "res.config.settings"
        ]._get_search_panel_field_ids()

        fields = self.env["ir.model.fields"].search(
            [
                ("id", "in", search_panel_field_ids),
                ("model", "=", self._name),
            ]
        )

        if not fields:
            return arch

        eview = etree.fromstring(arch)

        search_panels = eview.xpath("//searchpanel")

        if len(search_panels) == 0:
            search_panel = etree.Element("searchpanel")
        else:
            search_panel = search_panels[0]

        for field in fields:
            efield = etree.Element("field", name=field.name)
            search_panel.insert(0, efield)

        eview.insert(0, search_panel)

        return etree.tostring(eview, pretty_print=True)

    @api.model
    def web_search_read(
        self,
        domain=None,
        fields=None,
        offset=0,
        limit=None,
        order=None,
        count_limit=None,
    ):
        """
        Due to the search panel implementation, we can't use False as a boolean value.
        So we use "True" and "False" as string values and we convert them to boolean.
        """
        new_domain = []
        for leaf in domain:
            if len(leaf) < 3:
                new_domain.append(leaf)
                continue
            field, operator, value = leaf
            field = self._fields.get(field, None)
            if field and field.type == "boolean" and not isinstance(value, bool):
                value = value == "True"
                leaf = (field.name, operator, value)
            new_domain.append(leaf)
        return super().web_search_read(
            domain=new_domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

    @api.model
    def _search_panel_boolean(self, field_name, **kwargs):
        field = self._fields[field_name]
        domain = self._build_doamin_search_panel(kwargs)
        # Expression gonna parse the domain and return a query object
        result = self.read_group(domain, [field_name], [field_name])
        distinct_values = [x[field_name] for x in result]
        selection = self._get_selection(field, field_name)
        return {
            "parent_field": False,
            "values": self._define_panel_values_labels(
                distinct_values, selection, field
            ),
        }

    @api.model
    def _build_doamin_search_panel(self, kwargs):
        domain = AND(
            [
                kwargs.get("search_domain", []),
                kwargs.get("model_domain", []),
                kwargs.get("category_domain", []),
                kwargs.get("filter_domain", []),
            ]
        )

        return domain

    @api.model
    def _define_panel_values_labels(self, distinct_values, values_label, field):
        panel_values_label = []
        for value, label in values_label:
            if value in distinct_values:
                if field.type == "boolean":
                    id_value = str(value)
                else:
                    id_value = value
                panel_values_label.append(
                    {
                        "id": id_value,
                        "display_name": label,
                    }
                )
        return panel_values_label

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        field = self._fields[field_name]
        if field.type in ("many2one", "selection"):
            return super().search_panel_select_range(field_name, **kwargs)

        return self._search_panel_boolean(field_name, **kwargs)

    @api.model
    def _get_selection(self, field, field_name):
        if field.type == "selection":
            selection = self.fields_get([field_name])[field_name]["selection"]
        elif field.type == "boolean":
            selection = [(True, _("Yes")), (False, _("No"))]
        return selection
