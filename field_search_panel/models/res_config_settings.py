from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    searchpanel_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="searchpanel_field_rel",
        column1="searchpanel_id",
        column2="field_id",
        string="Search Panel Fields",
        domain=[("ttype", "in", ("selection", "many2one", "boolean"))],
    )

    @api.model
    def _get_search_panel_field_ids(self):
        param = self.env["ir.config_parameter"].sudo()
        search_panel_field_ids = param.get_param(
            "field_selection.searchpanel_field_ids"
        )
        if search_panel_field_ids and not search_panel_field_ids == "[]":
            search_panel_field_ids = search_panel_field_ids[1:-1]
            return [int(x) for x in search_panel_field_ids.split(",")]
        return []

    @api.model
    def get_values(self):
        res = super().get_values()
        search_panel_field_ids = self._get_search_panel_field_ids()
        if search_panel_field_ids:
            res.update(searchpanel_field_ids=[[6, 0, search_panel_field_ids]])
        return res

    @api.model
    def set_values(self):
        res = super().set_values()
        IrConfigParameter = self.env["ir.config_parameter"].sudo()
        IrConfigParameter.set_param(
            "field_selection.searchpanel_field_ids", self.searchpanel_field_ids.ids
        )
        return res
