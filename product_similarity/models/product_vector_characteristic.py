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
                ["many2one", "many2many", "selection", "boolean"],
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
    value_name = fields.Text(compute="_compute_value_name")
    value_id_visible = fields.Boolean(compute="_compute_value_id_visible")
    possible_values_string = fields.Text(compute="_compute_possible_values_string")
    name = fields.Text(compute="_compute_name")

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
            "The given pair (field_id, value_id) already exists.",
        ),
        (
            "unique_vector_index",
            "UNIQUE(vector_index)",
            "There cannot be two characteristics pointing to the same index in the vector.",
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

    @api.depends("field_id", "value_id")
    def _compute_value_name(self):
        for record in self:
            possible_values = record.get_possible_values(record.field_id)
            if not possible_values:
                record.value_name = ""
            else:
                record.value_name = possible_values.get(record.value_id, "")

    @api.depends("field_id", "value_name")
    def _compute_name(self):
        for record in self:
            if record.field_id.ttype == "boolean":
                record.name = record.field_id.name
            else:
                record.name = f"{record.field_id.name} = '{record.value_name}'"

    @api.depends("field_id")
    def _compute_value_id_visible(self):
        for record in self:
            if not record.field_id or record.field_id.ttype == "boolean":
                record.value_id_visible = False
            else:
                record.value_id_visible = True

    @api.model
    def get_possible_values(self, field):
        if not field:
            return {}

        elif field.ttype == "boolean":
            return {}
        elif field.ttype == "selection":
            return {x[0]: x[1] for x in field.selection_ids.name_get()}
        else:
            model = self.get_related_model(field)
            return {x[0]: x[1] for x in self.env[model.model].search([]).name_get()}

    @api.depends("field_id")
    def _compute_possible_values_string(self):
        for record in self:
            possible_values = record.get_possible_values(record.field_id)
            if possible_values:
                record.possible_values_string = "\n".join(
                    f"{value_id: <4n} {value_name}"
                    for value_id, value_name in sorted(possible_values.items())
                )
            else:
                record.possible_values_string = ""

    @api.model
    def get_related_model(self, field):
        if field.ttype in ["many2one", "one2many", "many2many"]:
            return self.env["ir.model"].search(
                [("model", "=", field.relation)], limit=1
            )
        elif field.ttype in ["boolean", "selection"]:
            return self.env["ir.model"].search(
                [("model", "=", "product.product")], limit=1
            )
        else:
            return False

    @api.depends("field_id")
    def _compute_model_id(self):
        for record in self:
            record.model_id = record.get_related_model(record.field_id)

    @api.constrains("value_id")
    def _check_value_id(self):
        for record in self:
            possible_values = record.get_possible_values(record.field_id)
            if not possible_values:
                continue
            possible_ids = list(possible_values)
            if record.value_id not in possible_ids:
                raise UserError(
                    _("The given value_id is not inside the possible value_id's")
                )

    @api.model
    def _get_empty_index(self, already_assigned_indices=None):
        stored_indices = [
            x["vector_index"] for x in self.search_read([], ["vector_index"])
        ]
        indices = stored_indices + (
            already_assigned_indices if already_assigned_indices else []
        )
        if not indices:
            return 0
        for i, index in enumerate(sorted(set(indices))):
            if i != index:
                return i
        return len(indices)

    @api.model_create_multi
    def create(self, vals_list):
        # Be sure to check fo an empty index BEFORE creating
        # the record
        already_assigned_indices = []
        for vals in vals_list:
            index = self.env["product.vector.characteristic"]._get_empty_index(
                already_assigned_indices
            )
            vals["vector_index"] = index
            already_assigned_indices.append(index)
        res = super().create(vals_list)
        return res

    def field_vectorization_wizard_action(self):
        """
        Returns the window action for the 'res.partner' model.
        """
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.field.vectorization.wizard",
            "views": [[False, "form"]],
            "target": "new",
        }
