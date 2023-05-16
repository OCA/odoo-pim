import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import TERM_OPERATORS
from odoo.osv.query import Query
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

JSON_DOMAIN_OPERATORS = tuple(
    filter(lambda x: x not in ["child_of", "not child_of"], TERM_OPERATORS)
)


class PimMixin(models.AbstractModel):
    _name = "pim.mixin"
    _description = "Mixin PIM"

    json_attributes_set = fields.Json("Json that store the attributes")

    _json_attributes_set_name = "json_attributes_set"

    @api.model
    def _setup_complete(self):
        """
        After a stop of odoo we need to reload all attribute into the model
        """
        attributes = self.env["attribute.attribute"].search(
            [
                ("relation_model_id.model", "=", self._name),
                ("nature", "=", "json_postgresql"),
            ]
        )
        logging.debug("Initializing %s attribute(s)", len(attributes))
        for attribute in attributes:
            self._set_compute_inverse_search(attribute)
        return super()._setup_complete()

    @api.model
    def _pop_attribute(self, name):
        """
        name: name of the property we want to remove
        """
        delattr(type(self), name)

    @api.model
    def _set_attribute(self, name, value):
        """
        name: The name of the property we want to set
        value : any
        """
        cls = type(self)
        if not getattr(cls, name, False):
            setattr(cls, name, value)

    def _inverse_attribute(self, attribute_id):
        """Generic function to inverse an attribute store in the json."""
        attribute = self.env["attribute.attribute"].search([("id", "=", attribute_id)])
        for record in self:
            attr_key = attribute.name
            attribute_values = record[self._json_attributes_set_name]
            if attribute.translate:
                record[
                    self._json_attributes_set_name
                ] = record._inverse_translate_attribute(
                    attr_key, record, attribute_values
                )
            else:
                record[
                    self._json_attributes_set_name
                ] = record._inverse_attribute_not_translate(
                    attribute_values, attr_key, record
                )

    def _inverse_attribute_not_translate(self, attribute_values, attr_key, record):
        if not attribute_values:
            attribute_values = {attr_key: record[attr_key]}
        else:
            attribute_values.update({attr_key: record[attr_key]})
        return attribute_values

    def _inverse_translate_attribute(self, attr_key, record, attribute_values):
        lang = record.env.lang if record.env.lang else "en_US"
        if not attribute_values:
            return {attr_key: {lang: record[attr_key]}}

        if not attribute_values.get(attr_key, False):
            attribute_values.update({attr_key: {lang: record[attr_key]}})
        else:
            attribute_values[attr_key].update({lang: record[attr_key]})
        return attribute_values

    def _compute_attribute(self, attribute_id):
        """
        Generic function to compute an attribute we get the value from the json field and set it
        """
        attribute = self.env["attribute.attribute"].search([("id", "=", attribute_id)])
        for record in self:
            attr_key = attribute.name

            if not record[self._json_attributes_set_name]:
                record[attr_key] = False
                return

            attribute_value = record[self._json_attributes_set_name].get(attr_key)
            if attribute.translate:
                lang = record.env.lang if record.env.lang else "en_US"
                value_translated = (
                    attribute_value.get(lang, None) if attribute_value else False
                )
                if value_translated is None:
                    record[attr_key] = False
                else:
                    record[attr_key] = value_translated
            else:
                if attribute.attribute_type == "selection" and attribute_value not in [
                    x[0]
                    for x in self.fields_get([attribute.name])[attribute.name][
                        "selection"
                    ]
                ]:
                    # In case of the option has been deleted from the selection
                    record[attr_key] = ""
                else:
                    record[attr_key] = attribute_value

    @api.model
    def _set_compute_inverse_search(self, attribute):
        """
        set the odoo field and the compute inverse and search function
        as _[search|compute|inverse]_key
        These fonction will call the generic one to do the action passing the attribute_id
        attribute : attribute.attribute record
        field : Odoo field (ex: Char, Text, Integer, ...)
        """
        self._set_attribute(
            f"_search_{attribute.name}",
            lambda record, operator, value, attribute_id=attribute.id: record._search_attribute(
                operator, value, attribute_id
            ),
        )
        self._set_attribute(
            f"_compute_{attribute.name}",
            lambda record, attribute_id=attribute.id: record._compute_attribute(
                attribute_id
            ),
        )
        self._set_attribute(
            f"_inverse_{attribute.name}",
            lambda record, attribute_id=attribute.id: record._inverse_attribute(
                attribute_id
            ),
        )

    @api.model
    def _remove_attribute_as_field(self, key):
        self._pop_attribute(f"_compute_{key}")
        self._pop_attribute(f"_inverse_{key}")
        self._pop_attribute(f"_search_{key}")

    def _search_attribute(self, operator, value, attribute_id):
        if operator not in JSON_DOMAIN_OPERATORS:
            raise UserError(_("Operator %s not supported") % operator)
        attribute = self.env["attribute.attribute"].search([("id", "=", attribute_id)])
        if self._to_flush(attribute):
            self.flush_model()

        mixin_ids = self._query_mixin_ids(attribute, operator, value)

        return [("id", "in", mixin_ids)]

    def _to_flush(self, attribute):
        """
        Check if the fields is dirty in cache
        If a field is dirty we need to flush it before searching in the json
        because the value is not yet in the database
        """

        to_flush = False
        self.search([], limit=10).read()
        cache_data = self.env.cache._data.items()
        for field_name in cache_data:
            if field_name == attribute.field_id.name:
                to_flush = True
                break
        return to_flush

    def _query_mixin_ids(self, attribute, operator, value):
        where_clause, params = self._generate_query_sql(attribute, operator, value)
        where_clause = (
            "r.attribute_set_id = p.attribute_set_id and r.attribute_id = %s and "
            + where_clause
        )
        params = [attribute.id] + params
        query_obj = Query(self.env.cr, "p", self._table)
        query_obj.add_table(
            "r",
            "rel_attribute_set",
        )
        query_obj.add_where(where_clause, params)
        query, params = query_obj.select()
        self.env.cr.execute(query, params=params)
        mixin_ids = self.env.cr.fetchall()
        return mixin_ids

    def _generate_query_sql(self, attribute, operator, value):
        """
        attribute : attribute.attribute record
        operator: Domain operator
        value: value to search
        """
        if operator in ("in", "not in"):
            search = tuple(value)
        elif operator in ("like", "ilike", "not like", "not ilike") and value:
            search = f"%{value}%"
        else:
            search = value

        if operator in ("=like", "=ilike"):
            # Remove the = because =like isn't a sql operator.
            # In Odoo, like is for a full text search and =like is for a
            # a perfect match.
            operator = operator[1:]
        if attribute.translate:
            lang = self.env.lang or "en_US"
            where_clause = (
                f"COALESCE((p.{self._json_attributes_set_name}  -> %s ->> %s),"
                f"(p.{self._json_attributes_set_name}  -> %s ->> %s) ,%s) {operator} %s"
            )
            query_params = [attribute.name, lang, attribute.name, "en_US", "", search]
            return where_clause, query_params

        if attribute.attribute_type == "integer":
            cast = "::integer"
            default = 0
        elif attribute.attribute_type in ("float", "monetary"):
            cast = "::float"
            default = 0.0
        elif attribute.attribute_type == "boolean":
            cast = "::boolean"
            default = False
        else:
            cast = "::text"
            default = ""

        where_clause = (
            f"COALESCE((p.{self._json_attributes_set_name}  ->> %s)"
            f"{cast}, %s) {operator} %s"
        )
        query_params = [attribute.name, default, search]
        return where_clause, query_params

    def _update_field_translations(self, field_name, translations, digest=None):
        """
        Override to update the json field when we update
        the translation of a field using our inverse function
        """
        if self._fields[field_name].translate and self._fields[field_name].inverse:
            for record in self:
                for lang, value in translations.items():
                    record.with_context(lang=lang)[field_name] = value
            return True
        return super()._update_field_translations(field_name, translations, digest)
