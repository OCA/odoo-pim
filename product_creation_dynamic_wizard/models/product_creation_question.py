# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCreationQuestion(models.Model):
    _name = "product.creation.question"
    _inherit = [
        "mail.thread",
    ]
    _description = "Product creation question"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "sequence, complete_name"

    _sql_constraints = [
        (
            "question_set",
            "CHECK(is_automatic OR COALESCE(question, '') != '')",
            _("Question is required if step is not automatic"),
        )
    ]
    name = fields.Char(
        required=True,
        index=True,
        help="Technical name used to help organized questions.",
    )
    question = fields.Char(
        translate=True, tracking=True, help="The question displayed to the end user"
    )
    complete_name = fields.Char(
        compute="_compute_complete_name", store=True, recursive=True
    )
    parent_id = fields.Many2one(
        "product.creation.question",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(
        index=True,
    )
    child_ids = fields.One2many(
        "product.creation.question", "parent_id", string="Child questions"
    )
    sequence = fields.Integer(index=True, default=10)
    active = fields.Boolean(default=True, tracking=True)
    answer_required = fields.Boolean(
        default=True,
        tracking=True,
        help="Does a response is required on the current question?",
    )
    question_type = fields.Selection(
        [
            ("field", "Field"),
            ("custom", "Custom"),
            ("logical", "Logical"),
        ],
        required=True,
        tracking=True,
        default="field",
        help=(
            "Kind of questions: \n"
            "* **field**: Used to set a product field value (can be a node as well)\n"
            "* **custom**: Usefull for nodes to ask question not "
            "related to product field\n"
            "* **logical**: Logical nodes that allows to set multiple values as "
            "default value or as new value\n"
        ),
    )

    # question_type == 'field' fields
    field_id = fields.Many2one(
        "ir.model.fields",
        tracking=True,
        domain=[("model", "in", ["product.template", "product.product"])],
    )
    display_field_name = fields.Boolean(
        help="If check, display the label field in the wizard."
    )
    default_field_value = fields.Text(
        string="Default value",
        tracking=True,
        help="Default value for the field",
    )
    custom_view = fields.Text(tracking=True, help="If set use the definition as it.")

    # question_type == 'custom' fields
    answer_ids = fields.One2many(
        "product.creation.answer",
        "question_id",
        copy=True,
        help="Answers for the question",
    )
    default_answer_id = fields.Many2one(
        "product.creation.answer",
        string="Default answer",
        tracking=True,
    )

    # question_type == "logical"
    logical_default_values = fields.Text(
        help=(
            "Default values are used only if values are not set. "
            "Expected a valid json format, before parsing json "
            "special variables are replaced (ie: current_company_id)"
        )
    )
    logical_values = fields.Text(
        help=(
            "Those values will erase existing values. "
            "Expected a valid json format, before parsing json "
            "special variables are replaced (ie: current_company_id)"
        )
    )

    conditional_question = fields.Boolean(
        string="Is conditional",
        compute="_compute_conditional_question",
        default=False,
        store=True,
        readonly=False,
        tracking=True,
        help="What ever the question depends on a previous fields value",
    )
    parent_question_type = fields.Selection(
        related="parent_id.question_type", string="Parent type"
    )
    conditional_operator = fields.Selection(
        [
            ("==", "=="),
            ("!=", "!="),
        ],
        required=True,
        tracking=True,
        default="==",
        help="Operator to use",
    )
    conditional_expected_result = fields.Char(
        string="Expected result on parent question",
        tracking=True,
        help="If parent response is match run the current node and childs",
    )
    conditional_expected_result_answer_id = fields.Many2one(
        "product.creation.answer",
        tracking=True,
        string="Expected answer on parent question",
    )
    is_automatic = fields.Boolean(
        compute="_compute_is_automatic",
        store=True,
        readonly=False,
        tracking=True,
        help=(
            "If checked, the question will be automatically "
            "processed with the given default value without "
            "asking the user for a value."
        ),
    )
    automatic_save = fields.Boolean(
        string="Automatic save",
        default=False,
        help="If checked, the product will be saved at this step automatically.",
    )

    @api.model
    def _validate_xml_view(self, xml_view, fieldname):
        if xml_view:
            try:
                etree.fromstring(xml_view)
            except etree.XMLSyntaxError as ex:
                raise ValidationError(
                    _(
                        "Incorrect XML data - field '%(field_name)s':\n"
                        "Error:\n"
                        "%(error)s\n"
                        "Incorrect data: \n"
                        "%(data)s"
                    )
                    % {
                        "field_name": self._fields[fieldname].string,
                        "data": xml_view,
                        "error": ex,
                    }
                ) from ex

    @api.model
    def _validate_json(self, data, fieldname):
        if data:
            try:
                json.loads(data)
            except json.decoder.JSONDecodeError as ex:
                raise ValidationError(
                    _(
                        "Incorrect JSON data - field; '%(field_name)s':\n"
                        "Error:\n"
                        "%(error)s\n"
                        "Incorrect data: \n"
                        "%(data)s"
                    )
                    % {
                        "field_name": self._fields[fieldname].string,
                        "data": data,
                        "error": ex,
                    }
                ) from ex

    @api.constrains("custom_view")
    def _validate_custom_view(self):
        for rec in self:
            self._validate_xml_view(rec.custom_view, "custom_view")

    @api.constrains("logical_default_values")
    def _validate_logical_default_values(self):
        for rec in self:
            self._validate_json(rec.logical_default_values, "logical_default_values")

    @api.constrains("logical_values")
    def _validate_logical_values(self):
        for rec in self:
            self._validate_json(
                rec.logical_values
                and rec.logical_values.replace(
                    "current_company_id", str(self.env.company.id)
                ),
                "logical_values",
            )

    @api.depends("question_type")
    def _compute_is_automatic(self):
        for question in self:
            if question.question_type == "logical":
                question.is_automatic = True
            else:
                question.is_automatic = False

    @api.depends("parent_id", "parent_id.question_type")
    def _compute_conditional_question(self):
        for question in self:
            if question.parent_id and question.parent_id.question_type != "logical":
                question.conditional_question = question.conditional_question
            else:
                question.conditional_question = False

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for question in self:
            if question.parent_id:
                question.complete_name = "{} / {}".format(
                    question.parent_id.complete_name, question.name
                )
            else:
                question.complete_name = question.name
