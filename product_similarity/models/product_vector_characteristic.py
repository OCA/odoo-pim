from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


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
        string="Attribute Value",
        model_field="model_id",
        help="The id of the specific value of the characteristic from the linked model.\n"
        "For example, if the characteristic's model is \"Color(0: 'red', 1: 'green', 2: 'blue')\", "
        "then to represent the color 'green', you would choose `1`.",
    )

    weight = fields.Float(
        required=True,
        default=1,
        help="Weight applied to the current characteristic's index when computing "
        "vector distances.",
    )

    vector_index = fields.Integer(
        string="Vector Index",
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

    def _get_attribute_names(self):
        self.ensure_one()
        if not self.field_id:
            return []
        return []

    def _compute_vector_index(self):
        for record in self:
            record.vector_index = record._get_empty_index()

    @api.depends("field_id")
    def _compute_model_id(self):
        for record in self:
            if record.field_id.ttype in ["many2one", "one2many", "many2many"]:
                record.model_id = self.env["ir.model"].search(
                    [("model", "=", record.field_id.relation)], limit=1
                )
            elif record.field_id.ttype in ["boolean"]:
                record.model_id = self.env["ir.model"].search(
                    [("model", "=", "product.product")], limit=1
                )
            else:
                record.model_id = False

    @api.constrains("field_id")
    def _check_field(self):
        """
        Ensure field_id is a field linked to the `product.product` model.
        """
        for record in self:
            # TODO: ensure this references a product.product field
            pass

    @api.model
    def _get_effective_id(self, record):
        """
        Returns the effective integer ID of the given record.

        This method provides a consistent integer identifier for a record,
        whether it has been committed to the database (and thus has a real
        database ID) or is a new record still in the current transaction
        (represented by an Odoo `NewId` object).

        This method prevents issues caused by `models.NewId` objects being coerced into `0`
        when converted to an integer, which can lead to unique constraint violations or other unexpected behavior.
        """
        record.ensure_one()

        if isinstance(record.id, models.NewId):
            return record.id.origin

        return record.id

    def _to_cache_key(self):
        """Returns the cache key for a characteristic from this model."""
        self.ensure_one()
        return (
            self.value_res_model,
            self.value_res_id,
            self.field_id.id,
        )

    def _attribute_to_cache_key(self, attribute, field_name):
        """Returns the cache key for a characteristic from another model."""
        field_id = self.env["ir.model.fields"]._get("product.product", field_name).id
        return (attribute._name, self._get_effective_id(attribute), field_id)

    @api.model
    @tools.ormcache()
    def _get_vector_index_map(self):
        records = self.search([])
        return {
            r._to_cache_key(): {
                "index": r.vector_index,
                "weight": r.weight,
            }
            for r in records
        }

    def _get_empty_index(self):
        """
        Gets an empty index by returning the smallest positive integer in the range [0, max(indices) + 1].

        that is not present in the given list.
        """
        indices = [x["vector_index"] for x in self.search_read([], ["vector_index"])]
        if not indices:
            return 0
        for i, index in enumerate(sorted(indices)):
            if i != index:
                return i
        return len(indices)

    @api.model
    def _get_vector_index_and_weight(self, attribute, field_name, weight=None):
        """
        Gets the index of the given characteristic in the characteristics vector of product.product.

        This function creates the entry in db if no line exists yet in the table.
        """
        if len(attribute) != 1:
            raise ValueError(
                f"There should be exactly one attribute but given {len(attribute)}."
            )

        index_map = self._get_vector_index_map()
        cache_key = self._attribute_to_cache_key(attribute, field_name)
        _, _, field_id = cache_key
        index_and_weight = index_map.get(
            cache_key,
            {
                "index": -1,
                "weight": weight if weight else 1,
            },
        )
        index = index_and_weight["index"]

        # when index for this characteristic is not yet in db, create the entry
        if index < 0:
            index = self._get_empty_index()
            try:
                self.create(
                    [
                        {
                            "value_res_model": attribute._name,
                            "value_res_id": self._get_effective_id(attribute),
                            "field_id": field_id,
                            "weight": index_and_weight["weight"],
                            "vector_index": index,
                        }
                    ]
                )
            except Exception as e:
                raise e

        return (index, index_and_weight["weight"])

    @api.model
    def get_vector_indices_and_weights(
        self,
        records,
        fields_names,
        weights=None,
    ):
        """
        Get the indices of the given characteristics in the characteristics vector of product.product.

        This function creates the entries in db if no line exists yet in the table.
        """
        if weights is None:
            weights = [1 for _ in range(len(records))]
        return {
            (r, name): self._get_vector_index_and_weight(r, name, weight)
            for r, name, weight in zip(records, fields_names, weights, strict=True)
        }

    @api.model
    def get_number_indexed_characteristics(self):
        """Returns the number of characteristics currently indexed (ie the number of records in this model)."""
        return len(self._get_vector_index_map())

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.vector_index = record._get_empty_index()
        self._get_vector_index_map.clear_cache(self)
        return res

    def write(self, vals):
        res = super().write(vals)
        self._get_vector_index_map.clear_cache(self)
        return res

    def unlink(self):
        res = super().unlink()
        self._get_vector_index_map.clear_cache(self)
        return res
