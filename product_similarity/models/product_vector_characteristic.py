from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductVectorCharacteristic(models.Model):
    """
    Each record on this model represent one characteristic used on products
    characteristics vector.

    The main idea of this model is to link each characteristic with a
    dimension and a weight inside the characteristics vector.
    """

    _name = "product.vector.characteristic"
    _description = "Product Vector Characteristic"

    field_id = fields.Many2one(
        "ir.model.fields",
        store=True,
        ondelete="cascade",
        string="Field",
        required=True,
        domain=[
            ("model", "=", "product.product"),
            (
                "ttype",
                "in",
                ["many2one", "one2many", "many2many", "selection", "boolean"],
            ),
        ],
        help="Field inside the `product.product` model linked to the current characteristic.",
    )
    model_id = fields.Many2one(
        "ir.model",
        compute="_compute_model_id",
        help="Model name of the given characteristic",
    )
    value_id = fields.Many2oneReference(
        model_field="model_id",
        help="The id of the specific value of the characteristic from the linked model.\n"
        "For example, if the characteristic's model is \"Color(0: 'red', 1: 'green', 2: "
        "'blue')\", then to represent the color 'green', you would choose `1`.",
    )
    value_id_visible = fields.Boolean(compute="_compute_value_id_visible")
    possible_values = fields.Json(compute="_compute_possible_values")
    possible_values_string = fields.Text(compute="_compute_possible_values_string")

    weight = fields.Float(
        required=True,
        default=1,
        help="Weight applied to the current characteristic's index when computing "
        "vector distances.",
    )

    vector_index = fields.Integer(
        readonly=True,
        help="Index of current characteristic inside the characteristics vector",
    )

    _sql_constraints = [
        (
            "unique_field_value",
            "UNIQUE(field_id, value_id)",
            "A characteristic should be uniquely determined by a product.product "
            "field and a value.",
        ),
        (
            "unique_vector_index",
            "UNIQUE(vector_index)",
            "There cannot be two characteristics pointing to the same index in the vector.\n"
            "The given pair (field_id, value_id) already exists.",
        ),
        (
            "check_vector_index_non_negative",
            "CHECK(vector_index >= 0)",
            "A vector index must be >= 0",
        ),
        (
            "check_weight_positive",
            "CHECK(weight > 0)",
            "weight must be > 0",
        ),
    ]

    @api.depends("field_id")
    def _compute_value_id_visible(self):
        for record in self:
            if not record.field_id or record.field_id.ttype == "boolean":
                record.value_id_visible = False
            else:
                record.value_id_visible = True

    @api.depends("model_id")
    def _compute_possible_values(self):
        for record in self:
            if not record.field_id:
                record.possible_values = []

            elif record.field_id.ttype == "boolean":
                record.possible_values = []
            elif record.field_id.ttype == "selection":
                record.possible_values = [
                    {"id": x[0], "name": x[1]}
                    for x in record.field_id.selection_ids.name_get()
                ]
            else:
                record.possible_values = [
                    {"id": x[0], "name": x[1]}
                    for x in self.env[record.model_id.model].search([]).name_get()
                ]

    @api.depends("possible_values")
    def _compute_possible_values_string(self):
        for record in self:
            if record.possible_values:
                record.possible_values_string = "\n".join(
                    f"{x['id']: <4n} {x['name']}"
                    for x in sorted(record.possible_values, key=lambda x: x["id"])
                )
            else:
                record.possible_values_string = ""

    @api.depends("field_id")
    def _compute_model_id(self):
        for record in self:
            if record.field_id.ttype in ["many2one", "one2many", "many2many"]:
                record.model_id = self.env["ir.model"].search(
                    [("model", "=", record.field_id.relation)], limit=1
                )
            elif record.field_id.ttype in ["boolean", "selection"]:
                record.model_id = self.env["ir.model"].search(
                    [("model", "=", "product.product")], limit=1
                )
            else:
                record.model_id = False

    @api.constrains("value_id")
    def _check_value_id(self):
        for record in self:
            if not record.field_id:
                continue
            possible_ids = [x["id"] for x in record.possible_values]
            if record.value_id not in possible_ids:
                raise UserError(
                    _("The given value_id is not inside the possible value_id's")
                )
