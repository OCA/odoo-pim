# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
import re

from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv.orm import setup_modifiers

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


def safe_column_name(string):
    """ Prevent portability problem in database column name
    with other DBMS system
    Use case : if you synchronise attributes with other applications """
    string = unidecode(string.replace(" ", "_").lower())
    return re.sub(r"[^0-9a-z_]", "", string)


class AttributeAttribute(models.Model):
    _name = "attribute.attribute"
    _description = "Attribute"
    _inherits = {"ir.model.fields": "field_id"}

    @api.model
    def _build_attribute_field(self, subgroup):
        """Return an etree 'field' element made of the current attribute 'self'
        and child of his etree group 'subgroup'"""
        self.ensure_one()
        parent = etree.SubElement(subgroup, "group", colspan="2")

        kwargs = {"name": "%s" % self.name}
        if self.ttype in ["many2many", "text"]:
            # Display field label above his value
            field_title = etree.SubElement(parent, "b", colspan="2")
            field_title.text = self.field_description
            kwargs["nolabel"] = "1"
            if self.ttype == "many2many":
                # TODO use an attribute field instead
                # to let user specify the widget. For now it fixes:
                # https://github.com/shopinvader/odoo-pim/issues/2
                kwargs["widget"] = "many2many_tags"

        if self.ttype in ["many2one", "many2many"]:
            if self.relation_model_id:
                # TODO update related attribute.option in cascade to allow
                # attribute.option creation from the field.
                kwargs["options"] = "{'no_create': True}"
                # attribute.domain is a string, it may be an empty list
                try:
                    domain = ast.literal_eval(self.domain)
                except ValueError:
                    domain = None
                if domain:
                    kwargs["domain"] = self.domain
                else:
                    # Display only options linked to an existing object
                    ids = [op.value_ref.id for op in self.option_ids if op.value_ref]
                    kwargs["domain"] = "[('id', 'in', %s)]" % ids
                # Add color options if the attribute's Relational Model
                # has a color field
                relation_model_obj = self.env[self.relation_model_id.model]
                if 'color' in relation_model_obj.fields_get().keys():
                    kwargs["options"] = "{'color_field': 'color', 'no_create': True}"
            else:
                kwargs["domain"] = "[('attribute_id', '=', %s)]" % (self.id)

        kwargs["context"] = "{'default_attribute_id': %s}" % (self.id)
        kwargs["required"] = str(self.required or self.required_on_views)

        field = etree.SubElement(parent, "field", **kwargs)
        setup_modifiers(field, self.fields_get(self.name))

        return field

    @api.model
    def _build_attributes_notebook(self, attribute_ids):
        """Return a main_group etree element made of sub_groups for each
        attribute_group."""
        main_group = etree.Element("group", name="attributes_group", col="4")
        groups = []

        for attribute in attribute_ids:
            att_group_name = attribute.attribute_group_id.name.capitalize()
            if att_group_name in groups:
                xpath = ".//group[@string='%s']" % (att_group_name)
                subgroup = main_group.find(xpath)
            else:
                subgroup = etree.SubElement(
                    main_group, "group", string=att_group_name, colspan="2")
                groups.append(att_group_name)

            attribute._build_attribute_field(subgroup)
        return main_group

    field_id = fields.Many2one(
        "ir.model.fields", "Ir Model Fields", required=True, ondelete="cascade"
    )

    attribute_type = fields.Selection(
        [
            ("char", "Char"),
            ("text", "Text"),
            ("select", "Select"),
            ("multiselect", "Multiselect"),
            ("boolean", "Boolean"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("binary", "Binary"),
            ("float", "Float"),
        ],
        "Type",
        required=True,
    )

    serialized = fields.Boolean(
        "JSON Field",
        # TODO : Improve this help, 'attribute_custom_tmpl' does not mean anything
        help="If serialized, the field will be stocked in the serialized "
        "field: attribute_custom_tmpl or attribute_custom_variant "
        "depending on the field based_on",
    )

    option_ids = fields.One2many(
        "attribute.option", "attribute_id", "Attribute Options"
    )

    create_date = fields.Datetime("Created date", readonly=True)

    relation_model_id = fields.Many2one("ir.model", "Relational Model")

    required_on_views = fields.Boolean(
        "Required (on views)",
        help="If activated, the attribute will be mandatory on the views, "
        "but not in the database",
    )

    attribute_set_ids = fields.Many2many(
        comodel_name="attribute.set",
        string="Attribute Sets",
        relation='rel_attribute_set',
        column1='attribute_id',
        column2='attribute_set_id',
    )

    attribute_group_id = fields.Many2one(
        "attribute.group", "Attribute Group", required=True, ondelete="cascade"
    )

    sequence = fields.Integer("Sequence",
                              help="The attribute's order in his group")

    @api.onchange("field_description")
    def onchange_field_description(self):
        if self.field_description and not self.create_date:
            self.name = unidecode(
                "x_" + safe_column_name(self.field_description)
            )

    @api.onchange("name")
    def onchange_name(self):
        name = self.name
        if not name.startswith("x_"):
            self.name = "x_%s" % name

    @api.onchange("relation_model_id")
    def relation_model_id_change(self):
        "Remove selected options as they would be inconsistent"
        self.option_ids = [(5, 0)]

    @api.onchange("domain")
    def domain_change(self):
        if self.domain != '':
            try:
                ast.literal_eval(self.domain)
            except ValueError:
                raise ValidationError(
                    _(
                        """ "{}" is an unvalid Domain name.\n
                        Specify a Python expression defining a list of triplets.\
                        For example : "[('color', '=', 'red')]" """.format(self.domain)
                    ),
                )
            # Remove selected options as the domain will predominate on actual options
            if self.domain != '[]':
                self.option_ids = [(5, 0)]

    @api.multi
    def button_add_options(self):
        self.ensure_one()
        # Before adding another option delete the ones which are linked
        # to a deleted object
        for option in self.option_ids:
            if not option.value_ref:
                option.unlink()
        # Then open the Options Wizard which will display an 'opt_ids' m2m field related
        # to the 'relation_model_id' model
        return {
            "context": "{'attribute_id': %s}" % (self.id),
            "name": _("Options Wizard"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "attribute.option.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model
    def create(self, vals):
        """ Create an attribute.attribute

        When a `field_id` is given, the attribute will be linked to the
        existing field. The use case is to create an attribute on a field
        created with Python `fields`.

        """
        if vals.get("field_id"):
            # When a 'field_id' is given, we create an attribute on an
            # existing 'ir.model.fields'.  As this model `_inherits`
            # 'ir.model.fields', calling `create()` with a `field_id`
            # will call `write` in `ir.model.fields`.
            # When the existing field is not a 'manual' field, we are
            # not allowed to write on it. So we call `create()` without
            # changing the fields values.
            field_obj = self.env["ir.model.fields"]
            field = field_obj.browse(vals["field_id"])

            if vals.get("serialized"):
                raise ValidationError(
                    _("Error"),
                    _(
                        "Can't create a serialized attribute on "
                        "an existing ir.model.fields (%s)"
                    )
                    % field.name,
                )

            if field.state != "manual":
                # The ir.model.fields already exists and we want to map
                # an attribute on it. We can't change the field so we
                # won't add the ttype, relation and so on.
                return super(AttributeAttribute, self).create(vals)

        if vals.get("relation_model_id"):
            model = self.env["ir.model"].browse(vals["relation_model_id"])
            relation = model.model
        else:
            relation = "attribute.option"

        attr_type = vals.get("attribute_type")

        if attr_type == "select":
            vals["ttype"] = "many2one"
            vals["relation"] = relation

        elif attr_type == "multiselect":
            vals["ttype"] = "many2many"
            vals["relation"] = relation
            # Specify the relation_table's name in case of m2m not serialized
            # to avoid creating the same default relation_table name for any attribute
            # linked to the same attribute.option or relation_model_id's model.
            if not vals.get("serialized"):
                att_model_id = self.env["ir.model"].browse(vals["model_id"])
                table_name = "x_" + att_model_id.model.replace(".", "_")\
                    + "_" + vals["name"]\
                    + "_" + relation.replace(".", "_")\
                    + "_rel"
                # avoid too long relation_table names
                vals['relation_table'] = table_name[0:60]

        else:
            vals["ttype"] = attr_type

        if vals.get("serialized"):
            field_obj = self.env["ir.model.fields"]

            serialized_fields = field_obj.search(
                [
                    ("ttype", "=", "serialized"),
                    ("model_id", "=", vals["model_id"]),
                    ("name", "=", "x_custom_json_attrs"),
                ]
            )

            if serialized_fields:
                vals["serialization_field_id"] = serialized_fields[0].id

            else:
                f_vals = {
                    "name": "x_custom_json_attrs",
                    "field_description": "Serialized JSON Attributes",
                    "ttype": "serialized",
                    "model_id": vals["model_id"],
                }

                vals["serialization_field_id"] = (
                    field_obj.with_context({"manual": True}).create(f_vals).id
                )

        vals["state"] = "manual"
        return super(AttributeAttribute, self).create(vals)

    @api.multi
    def write(self, vals):
        # Prevent from changing Attribute's type
        if "attribute_type" in list(vals.keys()):
            if self.search(
                [
                    ("attribute_type", "!=", vals["attribute_type"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        "Can't change the type of an attribute. "
                        "Please create a new one."
                    )
                )
            else:
                vals.pop("attribute_type")
        # Prevent from changing relation_model_id for multiselect Attributes
        # as the values of the existing many2many Attribute fields won't be
        # deleted if changing relation_model_id
        if "relation_model_id" in list(vals.keys()):
            if self.search(
                [
                    ("relation_model_id", "!=", vals["relation_model_id"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        """Can't change the attribute's Relational Model in order to
                        avoid conflicts with existing objects using this attribute.
                        Please create a new one."""
                    )
                )
        # Prevent from changing 'JSON Field'
        if "serialized" in list(vals.keys()):
            if self.search(
                [
                    ("serialized", "!=", vals["serialized"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        """It is not allowed to change the boolean 'JSON Field'.
                        A serialized field can not be change to non-serialized \
                        and vice versa."""
                    )
                )
        # Delete related attribute.option.wizard when deleting attribute.option
        if "option_ids" in list(vals.keys()) and self.relation_model_id:
            for option_change in vals["option_ids"]:
                if option_change[0] == 2:
                    self.env['attribute.option.wizard'].search(
                        [('attribute_id', 'in', self.ids)]
                    ).unlink()

        return super(AttributeAttribute, self).write(vals)

    @api.multi
    def unlink(self):
        """ Delete the Attribute's related field when deleting an Attribute"""
        for attribute in self:
            self.env['ir.model.fields'].search(
                [('id', '=', attribute.field_id.id)]
            ).unlink()

        return super(AttributeAttribute, self).unlink()
