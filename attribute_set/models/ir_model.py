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
        model = field_data.get("model")
        if name.startswith("x_") and model == "attribute.attribute":
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
