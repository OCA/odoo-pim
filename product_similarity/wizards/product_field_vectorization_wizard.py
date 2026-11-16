# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..models.product_vector_characteristic import VECTORIZABLE_FIELD_TYPES


class ProductFieldVectorizationWizard(models.TransientModel):
    _name = "product.field.vectorization.wizard"
    _description = "Product Field Vectorization Wizard"

    field_id = fields.Many2one(
        "ir.model.fields",
        required=True,
        ondelete="cascade",
        domain=[
            ("model", "=", "product.product"),
            ("ttype", "in", VECTORIZABLE_FIELD_TYPES),
        ],
    )
    weight = fields.Float(default=1, required=True)

    def put_in_vector_action(self):
        self.ensure_one()
        characteristic_model = self.env["product.vector.characteristic"]
        existing = characteristic_model.search([("field_id", "=", self.field_id.id)])
        if self.field_id.ttype == "boolean":
            vals_list = [] if existing else [{}]
        else:
            possible_values = characteristic_model.get_possible_values(self.field_id)
            existing_value_ids = set(existing.mapped("value_id"))
            vals_list = [
                {"value_id": value_id}
                for value_id in possible_values
                if value_id not in existing_value_ids
            ]
        for vals in vals_list:
            vals.update(field_id=self.field_id.id, weight=self.weight)
        characteristic_model.create(vals_list)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if vals_list else "warning",
                "title": self.env._("Vector Characteristics Created"),
                "message": self.env._(
                    "Created %(nb_new)s new vector characteristics.",
                    nb_new=len(vals_list),
                ),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
