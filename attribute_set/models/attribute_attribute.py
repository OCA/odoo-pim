# -*- coding: utf-8 -*-
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
    _order = "sequence_group,sequence,name"

    field_id = fields.Many2one(
        "ir.model.fields", "Ir Model Fields", required=True, ondelete="cascade"
    )
    copy = fields.Boolean()

    nature = fields.Selection(
        [("custom", "Custom"), ("native", "Native")],
        string="Attribute Nature",
        required=True,
        default="custom",
        store=True,
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
        ]
    )

    serialized = fields.Boolean(
        "Serialized",
        help="""If serialized, the attribute's field will be stored in the serialization
            field 'x_custom_json_attrs' (i.e. a JSON containing all the serialized fields
            values) instead of creating a new SQL column for this attribute's field.
            Useful to increase speed requests if creating a high number of attributes.""",
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
        relation="rel_attribute_set",
        column1="attribute_id",
        column2="attribute_set_id",
    )

    attribute_group_id = fields.Many2one(
        "attribute.group", "Attribute Group", required=True, ondelete="cascade"
    )

    sequence_group = fields.Integer(
        "Sequence of the Group",
        related="attribute_group_id.sequence",
        help="The sequence of the group",
        store="True",
    )

    sequence = fields.Integer(
        "Sequence in Group", help="The attribute's order in his group"
    )
    company_dependent = fields.Boolean()

    def _get_attrs(self):
        attrs = {
            "invisible": [
                ("attribute_set_id", "not in", self.attribute_set_ids.ids)
            ]
        }
        if self.required or self.required_on_views:
            attrs.update(
                {
                    "required": [
                        ("attribute_set_id", "in", self.attribute_set_ids.ids)
                    ]
                }
            )
        return attrs

    @api.model
    def _build_attribute_field(self, attribute_egroup):
        """Add an etree 'field' subelement (related to the current attribute 'self')
        to attribute_egroup, with a conditional invisibility based on its
        attribute sets."""
        self.ensure_one()
        kwargs = {"name": "%s" % self.name}
        kwargs["attrs"] = str(self._get_attrs())

        if self.readonly:
            kwargs["readonly"] = str(True)

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
                    ids = [
                        op.value_ref.id
                        for op in self.option_ids
                        if op.value_ref
                    ]
                    kwargs["domain"] = "[('id', 'in', %s)]" % ids
                # Add color options if the attribute's Relational Model
                # has a color field
                relation_model_obj = self.env[self.relation_model_id.model]
                if "color" in relation_model_obj.fields_get().keys():
                    kwargs[
                        "options"
                    ] = "{'color_field': 'color', 'no_create': True}"
            elif self.nature == "custom":
                # Define field's domain and context with attribute's id to go along with
                # Attribute Options search and creation
                kwargs["domain"] = "[('attribute_id', '=', %s)]" % (self.id)
                kwargs["context"] = "{'default_attribute_id': %s}" % (self.id)

        if self.ttype == "text":
            # Display field label above his value
            field_title = etree.SubElement(
                attribute_egroup, "b", colspan="2", attrs=kwargs["attrs"]
            )
            field_title.text = self.field_description
            kwargs["nolabel"] = "1"
            kwargs["colspan"] = "2"
            setup_modifiers(field_title)
        efield = etree.SubElement(attribute_egroup, "field", **kwargs)
        setup_modifiers(efield)

    @api.multi
    def _build_attribute_eview(self):
        """Return an 'attribute_eview' including all the Attributes (in the current
        recorset 'self') distributed in different 'attribute_egroup' for each
        Attribute's group.
        """
        attribute_eview = etree.Element(
            "group", name="attributes_group", col="4"
        )
        groups = []

        for attribute in self:
            att_group = attribute.attribute_group_id
            att_group_name = att_group.name.capitalize()
            if att_group in groups:
                xpath = ".//group[@string='{}']".format(att_group_name)
                attribute_egroup = attribute_eview.find(xpath)
            else:
                att_set_ids = []
                for att in att_group.attribute_ids:
                    att_set_ids += att.attribute_set_ids.ids
                # Hide the Group if none of its attributes are in
                # the destination object's Attribute set
                hide_domain = "[('attribute_set_id', 'not in', {})]".format(
                    list(set(att_set_ids))
                )
                attribute_egroup = etree.SubElement(
                    attribute_eview,
                    "group",
                    string=att_group_name,
                    colspan="2",
                    attrs="{{'invisible' : {} }}".format(hide_domain),
                )
                groups.append(att_group)

            setup_modifiers(attribute_egroup)
            attribute._build_attribute_field(attribute_egroup)

        return attribute_eview

    @api.onchange("model_id")
    def onchange_model_id(self):
        return {"domain": {"field_id": [("model_id", "=", self.model_id.id)]}}

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
        """
        Remove selected options as they would be inconsistent
        """
        self.option_ids = [(5, 0)]

    @api.onchange("domain")
    def domain_change(self):
        if self.domain not in ["", False]:
            try:
                ast.literal_eval(self.domain)
            except ValueError:
                raise ValidationError(
                    _(
                        """ "{}" is an unvalid Domain name.\n
                        Specify a Python expression defining a list of triplets.\
                        For example : "[('color', '=', 'red')]" """.format(
                            self.domain
                        )
                    )
                )
            # Remove selected options as the domain will predominate on actual options
            if self.domain != "[]":
                self.option_ids = [(5, 0)]

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

        - In case of a new "custom" attribute, a new field object 'ir.model.fields' will
        be created as this model "_inherits" 'ir.model.fields'.
        So we need to add here the mandatory 'ir.model.fields' instance's attributes to
        the new 'attribute.attribute'.

        - In case of a new "native" attribute, it will be linked to an existing
        field object 'ir.model.fields' (through "field_id") that cannot be modified.
        That's why we remove all the 'ir.model.fields' instance's attributes values
        from `vals` before creating our new 'attribute.attribute'.

        """
        if vals.get("nature") == "native":
            # Remove all the values that can modify the related native field
            # before creating the new 'attribute.attribute'
            for key in set(vals).intersection(
                self.env["ir.model.fields"]._fields
            ):
                del vals[key]
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
                table_name = (
                    "x_"
                    + att_model_id.model.replace(".", "_")
                    + "_"
                    + vals["name"]
                    + "_"
                    + relation.replace(".", "_")
                    + "_rel"
                )
                # avoid too long relation_table names
                vals["relation_table"] = table_name[0:60]

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
        attr = super(AttributeAttribute, self).create(vals)
        if attr.company_dependent:
            # reload the registry
            attr.field_id.pool.setup_models(self.env.cr, partial=(
                not attr.field_id.pool.ready))
            # update database schema of model and its descendant models
            models = attr.field_id.pool.descendants([attr.model_id._name], '_inherits')
            attr.field_id.pool.init_models(
                self.env.cr, models, dict(self.env.context, update_custom_fields=True))
            attr.field_id.pool.signal_registry_change()
        return attr

    @api.multi
    def _delete_related_option_wizard(self, option_vals):
        """ Delete the attribute's options wizards related to the attribute's options
        deleted after the write"""
        self.ensure_one()
        for option_change in option_vals:
            if option_change[0] == 2:
                self.env["attribute.option.wizard"].search(
                    [("attribute_id", "=", self.id)]
                ).unlink()

    @api.multi
    def _delete_old_fields_options(self, options):
        """Delete attribute's field values in the objects using our attribute
        as a field, if these values are not in the new Domain or Options list
        """
        self.ensure_one()
        custom_field = self.name
        for obj in self.env[self.model].search([]):
            if obj.fields_get(custom_field):
                for value in obj[custom_field]:
                    if value not in options:
                        if self.attribute_type == "select":
                            obj.write({custom_field: False})
                        elif self.attribute_type == "multiselect":
                            obj.write({custom_field: [(3, value.id, 0)]})

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
        # Prevent from changing 'Serialized'
        if "serialized" in list(vals.keys()):
            if self.search(
                [
                    ("serialized", "!=", vals["serialized"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        """It is not allowed to change the boolean 'Serialized'.
                        A serialized field can not be change to non-serialized \
                        and vice versa."""
                    )
                )
        # Set the new values to self
        res = super(AttributeAttribute, self).write(vals)

        for att in self:
            options = att.option_ids
            if self.relation_model_id:
                options = self.env[att.relation_model_id.model]
                if "option_ids" in list(vals.keys()):
                    # Delete related attribute.option.wizard if an attribute.option
                    # has been deleted
                    att._delete_related_option_wizard(vals["option_ids"])
                    # If there is still some attribute.option available, override
                    # 'options' with the objects they are refering to.
                    options = options.search(
                        [
                            (
                                "id",
                                "in",
                                [op.value_ref.id for op in att.option_ids],
                            )
                        ]
                    )
                if "domain" in list(vals.keys()):
                    try:
                        domain = ast.literal_eval(att.domain)
                    except ValueError:
                        domain = []
                    if domain:
                        # If there is a Valid domain not null, it means that there is
                        # no more attribute.option.
                        options = options.search(domain)
            # Delete attribute's field values in the objects using our attribute
            # as a field, if these values are not in the new Domain or Options list
            if {"option_ids", "domain"} & set(vals.keys()):
                att._delete_old_fields_options(options)

        return res

    @api.multi
    def unlink(self):
        """ Delete the Attribute's related field when deleting a custom Attribute"""
        fields_to_remove = self.filtered(
            lambda s: s.nature == "custom"
        ).mapped("field_id")
        res = super(AttributeAttribute, self).unlink()
        fields_to_remove.unlink()
        return res
