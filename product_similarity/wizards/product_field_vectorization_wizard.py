# wizards/product_field_wizard.py

from odoo import _, fields, models


class ProductFieldWizard(models.TransientModel):
    _name = "product.field.vectorization.wizard"
    _description = "Product Field vectorization Wizard"

    field_id = fields.Many2one(
        "ir.model.fields",
        required=True,
        domain=[
            ("model", "=", "product.product"),
            (
                "ttype",
                "in",
                ["many2one", "one2many", "many2many", "selection", "boolean"],
            ),
        ],
    )

    weight = fields.Float(default=1, required=True)

    def put_in_vector_action(self):
        self.ensure_one()
        possible_values = self.env["product.vector.characteristic"].get_possible_values(
            self.field_id
        )
        already_existing_value_ids = [
            y["value_id"]
            for y in self.env["product.vector.characteristic"].search_read(
                [("field_id", "=", self.field_id.id)], ["value_id"]
            )
        ]
        to_add_value_ids = [
            x for x in possible_values if x not in already_existing_value_ids
        ]
        nb_new = len(to_add_value_ids)
        if self.field_id.ttype == "boolean" and not already_existing_value_ids:
            self.env["product.vector.characteristic"].create(
                {"field_id": self.field_id.id, "weight": self.weight}
            )
            nb_new = 1
        elif to_add_value_ids:
            self.env["product.vector.characteristic"].create(
                [
                    {
                        "field_id": self.field_id.id,
                        "value_id": value_id,
                        "weight": self.weight,
                    }
                    for value_id in to_add_value_ids
                ]
            )

        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {
                "type": "success",
                "title": _("New Vector Characteristics Created Successfully"),
                "message": _(
                    "Created %(nb_new)s new Vector Characteristics.", nb_new=nb_new
                ),
                "sticky": True,
            },
        )
        return {"type": "ir.actions.act_window_close"}
