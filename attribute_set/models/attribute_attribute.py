# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
import re

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..utils.orm import setup_modifiers

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError as err:
    _logger.debug(err)


def safe_column_name(string):
    """Prevent portability problem in database column name
    with other DBMS system
    Use case : if you synchronise attributes with other applications"""
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

    nature = fields.Selection(
        [("custom", "Custom"), ("native", "Native")],
        string="Attribute Nature",
        required=True,
        default="custom",
    )

    attribute_type = fields.Selection(
        [
            ("char", "Char"),
            ("text", "Text"),
            ("select", "Select"),
            ("multiselect", "Multiselect"),
            ("boolean", "Boolean"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("binary", "Binary (file)"),
            ("image", "Image"),
        ],
    )

    serialized = fields.Boolean(
        help="""If serialized, the attribute's field will be stored in the serialization
            field 'x_custom_json_attrs' (i.e. a JSON containing all the serialized
            fields values) instead of creating a new SQL column for this
            attribute's field. Useful to increase speed requests if creating a
            high number of attributes.""",
    )

    option_ids = fields.One2many(
        "attribute.option", "attribute_id", "Attribute Options"
    )

    create_date = fields.Datetime("Created date", readonly=True)

    relation_model_id = fields.Many2one(
        "ir.model", "Relational Model", ondelete="cascade"
    )

    widget = fields.Char(help="Specify widget to add to the field on the views.")

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
    allowed_attribute_set_ids = fields.Many2many(
        comodel_name="attribute.set",
        compute="_compute_allowed_attribute_set_ids",
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

    def _get_attrs(self):
        attrs = {"invisible": f"attribute_set_id not in {self.attribute_set_ids.ids}"}
        if self.required or self.required_on_views:
            attrs.update(
                {"required": f"attribute_set_id in {self.attribute_set_ids.ids}"}
            )
        return attrs

    @api.model
    def _build_attribute_field(self, attribute_egroup):
        """Add field into given attribute group.

        Conditional invisibility based on its attribute sets.
        """
        self.ensure_one()
        kwargs = {"name": f"{self.name}"}
        attrs = self._get_attrs()
        if self.widget:
            kwargs["widget"] = self.widget
        if self.ttype == "binary":
            kwargs["filename"] = f"{self.name}_filename"
        if self.readonly:
            kwargs["readonly"] = str(True)

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
                    kwargs["domain"] = f"[('id', 'in', {ids})]"
                # Add color options if the attribute's Relational Model
                # has a color field
                relation_model_obj = self.env[self.relation_model_id.model]
                if "color" in relation_model_obj.fields_get().keys():
                    kwargs["options"] = "{'color_field': 'color', 'no_create': True}"
            elif self.nature == "custom":
                # Define field's domain and context with attribute's id to go along with
                # Attribute Options search and creation
                kwargs["domain"] = f"[('attribute_id', '=', {self.id})]"
                kwargs["context"] = f"{{'default_attribute_id': {self.id}}}"
            elif self.nature != "custom":
                kwargs["context"] = self._get_native_field_context()

        if self.ttype == "text":
            # Display field label above his value
            field_title = etree.SubElement(attribute_egroup, "b", colspan="2")
            field_title.text = self.field_description
            kwargs["nolabel"] = "1"
            kwargs["colspan"] = "2"
            setup_modifiers(field_title)
        if "invisible" in attrs:
            kwargs["invisible"] = attrs["invisible"]
            if "field_title" in locals():
                field_title.set("invisible", attrs["invisible"])
        if "required" in attrs:
            kwargs["required"] = attrs["required"]
        efield = etree.SubElement(attribute_egroup, "field", **kwargs)
        setup_modifiers(efield)
        if self.ttype == "binary":
            kwargs = {"name": f"{self.name}_filename"}
            kwargs["invisible"] = str(True)
            extra_efield = etree.SubElement(attribute_egroup, "field", **kwargs)
            setup_modifiers(extra_efield)

    def _get_native_field_context(self):
        return str(self.env[self.field_id.model]._fields[self.field_id.name].context)

    def _build_attribute_eview(self):
        """Generate group element for all attributes in the current recordset.

        Return an 'attribute_eview' including all the Attributes (in the current
        recorset 'self') distributed in different 'attribute_egroup' for each
        Attribute's group.
        """
        attribute_eview = etree.Element("group", name="attributes_group", col="4")
        groups = []
        for attribute in self:
            att_group = attribute.attribute_group_id
            att_group_name = att_group.name.capitalize()
            if att_group in groups:
                xpath = f".//group[@string='{att_group_name}']"
                attribute_egroup = attribute_eview.find(xpath)
            else:
                att_set_ids = []
                for att in att_group.attribute_ids:
                    att_set_ids += att.attribute_set_ids.ids
                # Hide the Group if none of its attributes are in
                # the destination object's Attribute set
                hide_condition = f"attribute_set_id not in {list(set(att_set_ids))}"
                attribute_egroup = etree.SubElement(
                    attribute_eview,
                    "group",
                    string=att_group_name,
                    colspan="2",
                    invisible=hide_condition,
                )
                groups.append(att_group)
            setup_modifiers(attribute_egroup)
            attribute_with_env = (
                attribute.sudo() if not attribute.check_access("read") else attribute
            )
            attribute_with_env._build_attribute_field(attribute_egroup)

        return attribute_eview

    def _get_attribute_set_allowed_model(self):
        return self.model_id

    @api.depends("model_id")
    def _compute_allowed_attribute_set_ids(self):
        AttributeSet = self.env["attribute.set"]
        for record in self:
            allowed_models = record._get_attribute_set_allowed_model()
            record.allowed_attribute_set_ids = AttributeSet.search(
                [("model_id", "in", allowed_models.ids)]
            )

    @api.onchange("model_id")
    def onchange_model_id(self):
        return {"domain": {"field_id": [("model_id", "=", self.model_id.id)]}}

    @api.onchange("field_description")
    def onchange_field_description(self):
        if self.field_description and not self.create_date:
            self.name = unidecode("x_" + safe_column_name(self.field_description))

    @api.onchange("name")
    def onchange_name(self):
        name = self.name
        if name and not name.startswith("x_"):
            self.name = f"x_{name}"

    @api.onchange("attribute_type")
    def onchange_attribute_type(self):
        if self.attribute_type == "multiselect":
            self.widget = "many2many_tags"
        elif self.attribute_type == "binary":
            self.widget = "binary"
        elif self.attribute_type == "image":
            self.widget = "image"

    @api.onchange("relation_model_id")
    def _onchange_relation_model_id(self):
        """Remove selected options as they would be inconsistent"""
        self.option_ids = [(5, 0)]

    @api.onchange("domain")
    def _onchange_domain(self):
        if self.domain not in ["", False]:
            try:
                ast.literal_eval(self.domain)
            except ValueError:
                raise ValidationError(
                    self.env._(
                        "`%(domain)s` is an invalid Domain name.\n"
                        "Specify a Python expression defining a list of triplets.\n"
                        "For example : `[('color', '=', 'red')]`",
                        domain=self.domain,
                    )
                ) from ValueError
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
            # context since 17.0 will be dropped in views
            # unless we suffix it's key with _view_ref
            "context": {"attribute_id_view_ref": self.id},
            "name": self.env._("Options Wizard"),
            "view_mode": "form",
            "res_model": "attribute.option.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Create an attribute.attribute

        - In case of a new "custom" attribute, a new field object 'ir.model.fields' will
        be created as this model "_inherits" 'ir.model.fields'.
        So we need to add here the mandatory 'ir.model.fields' instance's attributes to
        the new 'attribute.attribute'.

        - In case of a new "native" attribute, it will be linked to an existing
        field object 'ir.model.fields' (through "field_id") that cannot be modified.
        That's why we remove all the 'ir.model.fields' instance's attributes values
        from `vals` before creating our new 'attribute.attribute'.

        """
        for vals in vals_list:
            if vals.get("nature") == "native":
                # For native attributes, remove modifying values while keeping essential
                ir_model_fields = self.env["ir.model.fields"]
                # Remove fields that modify ir.model.fields characteristics
                # Keep field_id for linking, remove others
                fields_to_remove = set(vals).intersection(
                    set(ir_model_fields._fields.keys())
                )
                for key in fields_to_remove:
                    if key != "field_id":  # Preserve linking field_id
                        vals.pop(key, None)
                continue

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
                # to avoid creating the same default
                # relation_table name for any attribute
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

            elif attr_type == "image":
                vals["ttype"] = "binary"

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
                        field_obj.with_context(manual=True).create(f_vals).id
                    )

            vals["state"] = "manual"
        res = super().create(vals_list)
        binary_fields = res.filtered(lambda f: f.ttype == "binary")
        vals_list = []
        for binary_field in binary_fields:
            vals_list.append(
                {
                    "ttype": "char",
                    "name": f"{binary_field.name}_filename",
                    "field_description": f"Filename for {binary_field.name}",
                    "state": binary_field.state,
                    "create_date": binary_field.create_date,
                    "model_id": binary_field.model_id.id,
                }
            )
        if vals_list:
            self.env["ir.model.fields"].create(vals_list)
        return res

    def _get_filename_value(self, record):
        filename = f"{self.field_id.name}_filename"
        return record[filename]

    def _delete_related_option_wizard(self, option_vals):
        """Delete related attribute's options wizards."""
        self.ensure_one()
        for option_change in option_vals:
            if option_change[0] == 2:
                self.env["attribute.option.wizard"].search(
                    [("attribute_id", "=", self.id)]
                ).unlink()
                break

    def _delete_old_fields_options(self, options):
        """Delete outdated attribute's field values on existing records."""
        self.ensure_one()
        custom_field = self.name
        # Use search with batch processing to avoid performance issues
        domain = []
        batch_size = 1000
        offset = 0

        while True:
            batch = self.env[self.model].search(domain, offset=offset, limit=batch_size)
            if not batch:
                break
            for obj in batch:
                if obj.fields_get(custom_field):
                    for value in obj[custom_field]:
                        if value not in options:
                            if self.attribute_type == "select":
                                obj.write({custom_field: False})
                            elif self.attribute_type == "multiselect":
                                obj.write({custom_field: [(3, value.id, 0)]})
            offset += batch_size

    def write(self, vals):
        # Prevent from changing Attribute's type
        if "attribute_type" in list(vals.keys()):
            if self.search_count(
                [
                    ("attribute_type", "!=", vals["attribute_type"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    self.env._(
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
            if self.search_count(
                [
                    ("relation_model_id", "!=", vals["relation_model_id"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        """Can't change the attribute's Relational Model in order to
                        avoid conflicts with existing objects using this attribute.
                        Please create a new one."""
                    )
                )
        # Prevent from changing 'Serialized'
        if "serialized" in list(vals.keys()):
            if self.search_count(
                [("serialized", "!=", vals["serialized"]), ("id", "in", self.ids)]
            ):
                raise ValidationError(
                    self.env._(
                        """It is not allowed to change the boolean 'Serialized'.
                        A serialized field can not be change to non-serialized \
                        and vice versa."""
                    )
                )
        # For native attributes, remove field-related values to prevent
        # modification of base fields
        self._handle_native_attribute_updates(vals)

        # Set the new values to self
        res = super().write(vals)

        for att in self:
            options = att.option_ids
            if att.relation_model_id:
                options = self.env[att.relation_model_id.model]
                if "option_ids" in list(vals.keys()):
                    # If there is still some attribute.option available, override
                    # 'options' with the objects they are refering to.
                    options = options.search(
                        [("id", "in", [op.value_ref.id for op in att.option_ids])]
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

    def _handle_native_attribute_updates(self, vals):
        """Helper method to handle field updates for native attributes."""
        for att in self:
            if att.nature == "native":
                # Remove field-related keys that would modify the underlying
                # ir.model.fields record
                field_related_keys = {
                    "name",
                    "field_description",
                    "ttype",
                    "relation",
                    "size",
                    "required",
                    "readonly",
                    "translate",
                    "selection",
                    "domain",
                }
                for key in field_related_keys.intersection(set(vals.keys())):
                    vals.pop(key, None)

    def copy(self, default=None):
        """Ensure unique name when duplicating attribute."""
        default = default or {}
        if "name" not in default:
            # Get the original name and add a suffix to make it unique
            original_name = self.name
            counter = 1
            new_name = f"{original_name}_copy{counter}"

            # Keep incrementing counter until we find a unique name
            while self.search_count([("name", "=", new_name)]) > 0:
                counter += 1
                new_name = f"{original_name}_copy{counter}"

            default["name"] = new_name
        return super().copy(default)

    def unlink(self):
        """Delete the Attribute's related field when deleting a custom Attribute"""
        fields_to_remove = self.filtered(lambda s: s.nature == "custom").mapped(
            "field_id"
        )
        binaries = self.filtered(lambda s: s.attribute_type == "binary")
        if binaries:
            self.env["ir.model.fields"].search(
                [
                    ("name", "in", [f"{x.name}_filename" for x in binaries]),
                    ("model_id", "in", binaries.mapped("model_id").ids),
                    ("create_date", "in", binaries.mapped("create_date")),
                ]
            ).unlink()
        res = super().unlink()
        fields_to_remove.unlink()
        return res
