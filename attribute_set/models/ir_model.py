# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu).
# @author Cédric PIGEON <cedric.pigeon@acsone.eu>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    @api.model
    def _instanciate_attrs(self, field_data):
        attrs = super()._instanciate_attrs(field_data)
        name = field_data.get("name")
        if name.startswith("x_"):
            self.env.cr.execute(
                "SELECT COUNT(*) FROM pg_class WHERE relname = %s",
                ("attribute_attribute",),
            )
            attribute_table_exists = self.env.cr.fetchone()
            if attribute_table_exists[0]:
                field_id = field_data.get("id")
                self.env.cr.execute(
                    "SELECT company_dependent FROM attribute_attribute"
                    " WHERE field_id=%s",
                    (field_id,),
                )
                result = self.env.cr.fetchone()
                if result and result[0]:
                    attrs["company_dependent"] = True
        return attrs
