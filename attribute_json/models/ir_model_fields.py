from odoo import models


class IrModelFields(models.Model):
    _name = "ir.model.fields"
    _inherit = "ir.model.fields"

    def _instanciate_attrs(self, field_data):
        res = super()._instanciate_attrs(field_data)

        if res is None:
            return res

        field_id = field_data.get("id")
        query = """
        SELECT * from attribute_attribute where field_id = %s
        """
        self.env.cr.execute(query, (field_id,))
        attribute = self.env.cr.dictfetchone()
        if not attribute:
            return res

        if attribute and attribute["nature"] == "json_postgresql":
            res.update(
                {
                    "compute": f"_compute_{field_data.get('name')}",
                    "inverse": f"_inverse_{field_data.get('name')}",
                    "search": f"_search_{field_data.get('name')}",
                }
            )
        return res
