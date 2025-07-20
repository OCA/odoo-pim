# Copyright 2025 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from typing import List, Optional, Tuple
from uuid import uuid4

from lxml import etree

from odoo import _, api, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized


class WizardStep:
    record_id: int
    """id of the product.creation.question record"""
    env = None
    """Odoo environement"""
    parent_index: int = -1
    """parent position in the current question tree"""

    answer_id: Optional[int] = None
    """in case of custom question this will save the user
    answer"""

    def __init__(
        self,
        record_id: int,
        parent_index: int,
        answer_id: Optional[int] = None,
        odoo_env=None,
    ):
        self.record_id = record_id
        self.parent_index = parent_index
        self.answer_id = answer_id
        self.env = odoo_env

    @property
    def _record(self):
        return self.env["product.creation.question"].browse(self.record_id)

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "parent_index": self.parent_index,
            "answer_id": self.answer_id,
        }

    def __getattr__(self, name):
        return getattr(self._record, name)


class Wizard:

    steps: List[WizardStep] = None
    """list of ordered questions"""

    step_history: List[int] = None
    """steps processed by the user"""

    def __init__(self, steps: List[WizardStep] = None, step_history: List[int] = None):
        if not steps:
            steps = []
        if not step_history:
            step_history = []
        self.steps = steps
        self.step_history = step_history

    def append(self, step: WizardStep):
        self.steps.append(step)

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, position):
        return self.steps[position]

    @staticmethod
    def from_dict(data: dict, odoo_env) -> "Wizard":
        steps = [
            WizardStep(**step, odoo_env=odoo_env) for step in data.pop("steps", [])
        ]
        return Wizard(steps=steps, **data)

    def to_dict(self):
        return {
            "steps": [step.to_dict() for step in self.steps],
            "step_history": self.step_history,
        }


class ProductCreationDynamicWizard(models.TransientModel):
    _name = "product.creation.dynamic.wizard"
    _description = (
        "A dynamic wizard that helps user to create product "
        "based on business configuration"
    )

    wizard_steps = Serialized(default=lambda self: self._default_wizard_steps())
    product_data = Serialized(default=lambda self: self._default_product_data())
    current_step = fields.Integer(default=-1)
    current_question = fields.Char(compute="_compute_current_fields")
    current_complete_name = fields.Char(compute="_compute_current_fields")
    current_company_id = fields.Many2one(
        "res.company",
        compute="_compute_current_fields",
        help=(
            "Related to the current company_id that will be set on product"
            "which can be used in: \n"
            "* custom view while creating x2m object (ie: "
            "`contex=\"{'default_company_id': current_company_id}\"`)\n"
            "* in default values while creating x2m objects \n"
            "(ie: [[6,0,{'company_id': current_company_id}]])"
        ),
    )

    @api.model
    def _populate_wizard_steps(self, wizard: Wizard, question, parent_index=-1):
        index = len(wizard)
        wizard.append(
            WizardStep(
                record_id=question.id,
                parent_index=parent_index,
                odoo_env=self.env,
            )
        )
        for question in question.child_ids:
            self._populate_wizard_steps(wizard, question, parent_index=index)

    def _default_wizard_steps(self):
        wizard = Wizard()
        root_questions = self.env["product.creation.question"].search(
            [("parent_id", "=", False)]
        )
        for root_question in root_questions:
            self._populate_wizard_steps(wizard, root_question)
        return wizard.to_dict()

    @api.model
    def _default_product_data(self):
        return {
            "company_id": self.env.company.id,
        }

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id, view_type, toolbar=toolbar, submenu=False
        )
        if view_type == "form":
            self._apply_step(result)
        return result

    @api.model
    def _apply_step_field(self, current_step, node, result):
        if current_step.custom_view:
            node.append(etree.fromstring(current_step.custom_view))
        else:
            node.append(
                etree.Element(
                    "field",
                    name=current_step.field_id.name,
                    attrib={
                        "required": "1" if current_step.answer_required else "0",
                        "nolabel": "0" if current_step.display_field_name else "1",
                    },
                )
            )

        result["fields"].update(
            self.env[current_step.field_id.model].fields_get(
                allfields=[current_step.field_id.name]
            )
        )

    @api.model
    def _apply_step_custom(self, current_step, node, result):
        node.append(
            etree.Element(
                "field",
                name="answer_id",
                attrib={
                    "domain": f'[("question_id", "=", {current_step.record_id})]',
                    "options": "{'no_create': True, 'no_create_edit': True, 'no_open': True}",
                    "nolabel": "1",
                    "required": "1" if current_step.answer_required else "0",
                },
            )
        )
        result["fields"]["answer_id"] = self.env[
            "product.creation.question"
        ].fields_get(allfields=["default_answer_id"])["default_answer_id"]

    @api.model
    def _apply_step(self, result):
        doc = etree.fromstring(result["arch"])
        current_step = None
        if self.env.context.get("active_model") == self._name:
            wizard = self.browse(self.env.context.get("active_id"))
            if wizard.exists():
                wizard.refresh()
                current_step = wizard.step
        if not current_step:
            current_step = self.new().steps[0]
        for node in doc.xpath("//form/group[@name='question']"):
            if current_step.question_type == "field":
                self._apply_step_field(current_step, node, result)
            if current_step.question_type == "custom":
                self._apply_step_custom(current_step, node, result)

            self.env["ir.ui.view"].postprocess_and_fields(
                node, model=self._name, validate=False
            )

        result["arch"] = etree.tostring(doc, encoding="unicode")

    @api.model
    def _split_fieldnames(self, fields: List[str]) -> Tuple[List[str], List[str]]:
        wizard_fields = []
        other_fields = []
        for fieldname in fields:
            if fieldname in self._model_fields:
                wizard_fields.append(fieldname)
            else:
                other_fields.append(fieldname)
        return wizard_fields, other_fields

    @property
    def steps(self):
        """deserialize wizard_steps as Wizard object"""
        return Wizard.from_dict(self.wizard_steps or {}, self.env)

    @property
    def step(self):
        return self.steps[self.current_step]

    def _compute_current_fields(self):
        for wizard in self:
            wizard.current_question = wizard.step.question
            wizard.current_complete_name = wizard.step.complete_name
            wizard.current_company_id = int(
                wizard.product_data.get("company_id", self.env.company.id)
            )

    def read(self, fields=None, load="_classic_read"):
        if not fields:
            fields = []
        wizard_fields, other_fields = self._split_fieldnames(fields)
        answers_fields_only = bool(other_fields) and not bool(wizard_fields)
        if answers_fields_only:
            data = [{"id": record.id} for record in self]
        else:
            data = super().read(fields=wizard_fields, load=load)
        for datum in data:
            current_wizard = self.browse(datum["id"])
            current_step = current_wizard.step
            for fieldname in other_fields:
                if current_step.question_type == "field":
                    datum[fieldname] = current_wizard.product_data.get(fieldname, False)
                if current_step.question_type == "custom":
                    datum[fieldname] = (
                        (
                            current_step.answer_id,
                            self.env["product.creation.answer"]
                            .browse(current_step.answer_id)
                            .name,
                        )
                        if current_step.answer_id
                        else False
                    )
        return data

    def write(self, vals):
        wizard_fields, other_fields = self._split_fieldnames(vals.keys())
        res = super().write({k: v for k, v in vals.items() if k in wizard_fields})
        self.write_serialized_data({k: v for k, v in vals.items() if k in other_fields})
        return res

    def write_serialized_data(self, vals):
        if not vals:
            return

        for rec in self:
            answer_id = vals.pop("answer_id", False)
            if answer_id:
                wizard_data = rec.steps
                wizard_data[rec.current_step].answer_id = answer_id
                rec.write({"wizard_steps": wizard_data.to_dict()})

            if vals:
                data = rec.product_data
                data.update(vals)
                rec.write({"product_data": data})

    def _is_valid_chid_question(self, parent_wizard_step):
        """If there is a parent that has not been visited, the current
        child question is not a valid question."""
        if parent_wizard_step and self.step.parent_index not in self.steps.step_history:
            return False
        return True

    def _is_valid_condition(self, parent_wizard_step):
        if self.step.conditional_question and parent_wizard_step:
            answer = ""
            expected = ""
            if parent_wizard_step.question_type == "field":
                answer = str(
                    self.product_data.get(parent_wizard_step.field_id.name)
                ).lower()
                expected = str(self.step.conditional_expected_result).lower()

            if parent_wizard_step.question_type == "custom":
                answer = parent_wizard_step.answer_id
                expected = self.step.conditional_expected_result_answer_id.id

            if self.step.conditional_operator == "==" and answer != expected:
                return False

            if self.step.conditional_operator == "!=" and answer == expected:
                return False
        return True

    def _prepare_product_data(self):
        if self.step.question_type == "field":
            field_value = self.product_data.get(
                self.step.field_id.name, self.step.default_field_value
            )
            if isinstance(field_value, str):
                field_value = field_value.replace(
                    "current_company_id", str(self.current_company_id.id)
                )
            try:
                # useful for m2m with value such as [(0,0,{...})]
                field_value = json.loads(field_value)
            except Exception:
                pass
            return {self.step.field_id.name: field_value}

        if self.step.question_type == "custom" and self.step.answer_id is None:
            return {"answer_id": self.step.default_answer_id.id}

        if self.step.question_type == "logical":
            product_data = {}
            logical_default_values = self.step.logical_default_values or "{}"
            default_values = json.loads(logical_default_values)

            logical_values = self.step.logical_values or "{}"
            logical_values = logical_values.replace(
                "current_company_id", str(self.current_company_id.id)
            )
            values = json.loads(logical_values)

            for field_name in {*values.keys(), *default_values.keys()}:
                product_data[field_name] = values.get(
                    field_name,
                    self.product_data.get(
                        field_name,
                        default_values.get(
                            field_name,
                        ),
                    ),
                )
            return product_data
        return {}

    def get_next_action(self):
        user_step = False
        while not user_step:
            self.current_step += 1
            if self.current_step >= len(self.steps):
                break
            parent_wizard_step = None
            if self.step.parent_index >= 0:
                parent_wizard_step = self.steps[self.step.parent_index]

            if not self._is_valid_chid_question(parent_wizard_step):
                continue

            if not self._is_valid_condition(parent_wizard_step):
                continue

            self.write_serialized_data(self._prepare_product_data())
            if self.step.is_automatic:
                self._save_current_step_history()
                continue
            user_step = True

        if user_step:
            return self._open_wizard_action()
        return self.action_create()

    def _save_current_step_history(self):
        wizard_data = self.steps
        wizard_data.step_history.append(self.current_step)
        self.write({"wizard_steps": wizard_data.to_dict()})

    def action_open_next(self):
        self._save_current_step_history()
        return self.get_next_action()

    def action_open_previous(self):
        wizard_data = self.steps
        while wizard_data.step_history:
            self.current_step = wizard_data.step_history.pop()
            if not self.step.is_automatic:
                break
        self.write({"wizard_steps": wizard_data.to_dict()})
        return self._open_wizard_action()

    def _open_wizard_action(self):
        self.ensure_one()
        an_named_product_title = _("a new product")
        return {
            "name": _("Creating %(product_name)s...")
            % {
                "product_name": self.product_data.get("name", an_named_product_title)
                or an_named_product_title
            },
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "invalidate_cache": str(uuid4()),
                "product_creation_wizard": True,
            },
        }

    def _split_product_data(self):
        template_values = {}
        product_values = {}
        template_fields = self.env["product.template"]._model_fields
        for fieldname, value in self.product_data.items():
            if fieldname in template_fields:
                template_values[fieldname] = value
            else:
                product_values[fieldname] = value
        return template_values, product_values

    def _action_create(self):
        template_values, product_values = self._split_product_data()
        template = self.env["product.template"].create(template_values)
        template.product_variant_ids.write(product_values)
        return template

    def action_create(self):
        template = self._action_create()
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.template",
            "view_mode": "form",
            "view_type": "form",
            "res_id": template.id,
        }
