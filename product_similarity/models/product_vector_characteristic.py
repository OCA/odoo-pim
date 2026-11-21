# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

VECTORIZABLE_FIELD_TYPES = ["many2one", "many2many", "selection", "boolean"]


class ProductVectorCharacteristic(models.Model):
    """
    Each record on this model represent one characteristic used on products
    characteristics vector.

    The main idea of this model is to link each characteristic with a
    dimension and a weight inside the characteristics vector.
    """

    _name = "product.vector.characteristic"
    _description = "Product Vector Characteristic"
    _order = "vector_index"

    field_id = fields.Many2one(
        "ir.model.fields",
        ondelete="cascade",
        required=True,
        domain=[
            ("model", "=", "product.product"),
            ("ttype", "in", VECTORIZABLE_FIELD_TYPES),
        ],
        help="Field inside the `product.product` model linked to the current "
        "characteristic.",
    )
    model_id = fields.Many2one(
        "ir.model",
        compute="_compute_model_id",
        help="Model name of the given characteristic",
    )
    value_model = fields.Char(
        compute="_compute_value_model",
        help="Technical name of the model holding the values of the field",
    )
    selection_field_id = fields.Many2one(
        "ir.model.fields",
        compute="_compute_value_model",
        help="Field holding the selection values (the related field for related "
        "or inherited selection fields)",
    )
    field_type = fields.Selection(related="field_id.ttype")
    selection_value_id = fields.Many2one(
        "ir.model.fields.selection",
        compute="_compute_selection_value_id",
        inverse="_inverse_selection_value_id",
        domain="[('field_id', '=', selection_field_id)]",
        help="Value of the selection field linked to the current characteristic.",
    )
    value_id = fields.Many2oneReference(
        model_field="value_model",
        help="The id of the specific value of the characteristic from the linked "
        "model.\nFor example, if the characteristic's model is \"Color(0: 'red', "
        "1: 'green', 2: 'blue')\", then to represent the color 'green', you would "
        "choose `1`.",
    )
    value_name = fields.Text(compute="_compute_value_name")
    value_id_visible = fields.Boolean(compute="_compute_value_id_visible")
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

    _unique_field_value = models.Constraint(
        "UNIQUE(field_id, value_id)",
        "The given pair (field_id, value_id) already exists.",
    )
    _unique_vector_index = models.Constraint(
        "UNIQUE(vector_index)",
        "There cannot be two characteristics pointing to the same index in the vector.",
    )
    _check_vector_index_non_negative = models.Constraint(
        "CHECK(vector_index >= 0)",
        "A vector index must be >= 0",
    )
    _check_weight_positive = models.Constraint(
        "CHECK(weight > 0)",
        "Weight must be > 0",
    )

    @api.depends("field_id", "value_id")
    def _compute_value_name(self):
        for record in self:
            possible_values = record.get_possible_values(record.field_id)
            record.value_name = possible_values.get(record.value_id, "")

    @api.depends("field_id", "value_name")
    def _compute_name(self):
        for record in self:
            if not record.field_id:
                record.name = ""
            elif record.field_id.ttype == "boolean":
                record.name = record.field_id.name
            else:
                record.name = f"{record.field_id.name} = '{record.value_name}'"

    @api.depends("field_id")
    def _compute_value_id_visible(self):
        for record in self:
            record.value_id_visible = (
                bool(record.field_id) and record.field_id.ttype != "boolean"
            )

    @api.model
    def _get_selection_field(self, field):
        """Return the field holding the selection values of ``field``

        Related and inherited (e.g. from ``product.template``) selection fields
        do not have selection values of their own.
        """
        if not field or field.selection_ids or field.model not in self.env:
            return field
        orm_field = self.env[field.model]._fields[field.name]
        while orm_field.related_field is not None:
            orm_field = orm_field.related_field
        return field._get(orm_field.model_name, orm_field.name)

    @api.depends("field_id")
    def _compute_value_model(self):
        for record in self:
            field = record.field_id
            record.selection_field_id = False
            if field.ttype == "selection":
                record.value_model = "ir.model.fields.selection"
                record.selection_field_id = self._get_selection_field(field)
            elif field.ttype in ["many2one", "many2many"]:
                record.value_model = field.relation
            else:
                record.value_model = False

    @api.depends("field_id", "value_id")
    def _compute_selection_value_id(self):
        for record in self:
            if record.field_id.ttype == "selection" and record.value_id:
                record.selection_value_id = self.env[
                    "ir.model.fields.selection"
                ].browse(record.value_id)
            else:
                record.selection_value_id = False

    def _inverse_selection_value_id(self):
        for record in self:
            if record.field_id.ttype == "selection":
                record.value_id = record.selection_value_id.id

    @api.onchange("selection_value_id")
    def _onchange_selection_value_id(self):
        # keep value_id (and so the name) in sync before saving
        self._inverse_selection_value_id()

    @api.model
    def get_possible_values(self, field):
        """Return a {value_id: display name} dict of the values of ``field``"""
        if not field or field.ttype == "boolean":
            return {}
        if field.ttype == "selection":
            records = self._get_selection_field(field).selection_ids
        else:
            # every value of the related model is a candidate characteristic
            records = self.env[field.relation].search([])  # pylint: disable=no-search-all
        return {record.id: record.display_name for record in records}

    @api.model
    def get_related_model(self, field):
        if field.ttype in ["many2one", "many2many"]:
            return self.env["ir.model"]._get(field.relation)
        if field.ttype in ["boolean", "selection"]:
            return self.env["ir.model"]._get("product.product")
        return self.env["ir.model"]

    @api.depends("field_id")
    def _compute_model_id(self):
        for record in self:
            record.model_id = record.get_related_model(record.field_id)

    @api.constrains("field_id", "value_id")
    def _check_value_id(self):
        for record in self:
            possible_values = record.get_possible_values(record.field_id)
            if possible_values and record.value_id not in possible_values:
                raise ValidationError(
                    self.env._(
                        "The value %(value)s is not a possible value of field "
                        "%(field)s.",
                        value=record.value_id,
                        field=record.field_id.name,
                    )
                )

    @api.model
    def _get_empty_index(self, already_assigned_indices=None):
        [(stored_indices,)] = self._read_group([], [], ["vector_index:array_agg"])
        stored_indices = [i for i in stored_indices or [] if i is not None]
        indices = sorted(set(stored_indices + (already_assigned_indices or [])))
        for i, index in enumerate(indices):
            if i != index:
                return i
        return len(indices)

    @api.model
    def _selection_value_to_value_id(self, vals):
        # value_id must be set before the constraints are checked, which
        # happens before the inverse of selection_value_id is called
        if vals.get("selection_value_id"):
            vals["value_id"] = vals["selection_value_id"]
        return vals

    def write(self, vals):
        return super().write(self._selection_value_to_value_id(vals))

    @api.model_create_multi
    def create(self, vals_list):
        # Assign free indices before creating the records
        already_assigned_indices = []
        for vals in vals_list:
            self._selection_value_to_value_id(vals)
            index = self._get_empty_index(already_assigned_indices)
            vals["vector_index"] = index
            already_assigned_indices.append(index)
        return super().create(vals_list)
