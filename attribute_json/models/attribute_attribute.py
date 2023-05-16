from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import lazy_property
from odoo.tools.translate import _


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"
    _description = "Attribute"

    nature = fields.Selection(
        selection_add=[("json_postgresql", "Json_postgresql")],
        ondelete={"json_postgresql": "set default"},
    )

    attribute_type = fields.Selection(
        selection_add=[("monetary", "Monetary"), ("selection", "Selection")],
        ondelete={"monetary": "cascade"},
    )

    @api.model_create_multi
    def create(self, vals_list):
        attributes = super().create(vals_list)
        attributes._update_relation_model_attribute()
        return attributes

    def _update_relation_model_attribute(self):
        """
        Update the relation model with the new attribute
        We follow the same logic as the odoo core to create the field
        """
        to_refresh = False
        for attribute in self:
            if attribute.nature == "json_postgresql":
                to_refresh = True
                Record = self.env[attribute.relation_model_id.model]
                fields_data = self.env["ir.model.fields"]._get_manual_field_data(
                    Record._name
                )
                field_data = fields_data.get(attribute.name)
                try:
                    field = self.env["ir.model.fields"]._instanciate(field_data)
                    if field is not None:
                        # Not the best way.
                        # Odoo should add these attribute
                        field.depends = tuple()
                        field.depends_context = tuple()
                        Record._add_field(attribute.name, field)
                        self.env[
                            attribute.relation_model_id.model
                        ]._set_compute_inverse_search(attribute)
                except Exception as err:
                    raise ValidationError(
                        _(
                            "Failed to load field {field_name} on model {model_name}"
                        ).format(
                            field_name=attribute.name,
                            model_name=attribute.relation_model_id.model,
                        )
                    ) from err
        if to_refresh:
            # Refresh registry to update field_computed and field_inverse
            lazy_property.reset_all(self.env.registry)

    def unlink(self):
        to_remove = []
        for record in self:
            if record.nature == "json_postgresql":
                to_remove.append(
                    {
                        "name": record.name,
                        "model_name": record.relation_model_id.model,
                    }
                )
        res = super().unlink()
        if to_remove:
            for attribute_info in to_remove:
                self.env[attribute_info.get("model_name")]._remove_attribute_as_field(
                    attribute_info.get("name")
                )
            lazy_property.reset_all(self.env.registry)
        return res

    @api.constrains("field_id", "attribute_type", "translate")
    def _check_json_compliance(self):
        for record in self:
            if record.attribute_type != "json_postgresql":
                continue
            if record.attribute_type in ("integer", "float") and record.translate:
                raise ValidationError(_("You can not translate a numeric field"))
            if record.attribute_type in (
                "date",
                "datetime",
                "binary",
                "select",
                "multiselect",
            ):
                raise ValidationError(
                    _("Json attribute can't be of type %s") % record.attribute_type
                )

    def _update_field_vals_by_nature(self, vals):
        vals = super()._update_field_vals_by_nature(vals)
        if vals.get("nature") != "json_postgresql":
            return vals
        vals.pop("state")
        vals.update({"store": False, "state": "manual"})
        if not vals.get("relation_model_id"):
            vals.update(
                {
                    "relation_model_id": vals.get("model_id"),
                }
            )
        return vals
