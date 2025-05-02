import json

from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo.tests import Form, SavepointCase, tagged

from odoo.addons.product_creation_dynamic_wizard.wizards import (
    product_creation_dynamic_wizard as W,
)

Wizard = W.Wizard
WizardStep = W.WizardStep


@tagged("post_install", "-at_install")
class TestProductCreationDynamicWizardWithoutDemo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env["product.creation.question"].search([]).unlink()

    def test_force_false_value_in_logical_step(self):

        self.env["product.creation.question"].create(
            {
                "name": "Force false purchase ok",
                "question_type": "logical",
                "sequence": 5,
                "logical_values": '{"purchase_ok": false}',
            }
        )
        self.env["product.creation.question"].create(
            {
                "name": "default purchase ok should be ignored ignored",
                "question_type": "logical",
                "sequence": 10,
                "logical_default_values": '{"purchase_ok": true}',
            }
        )

        product_creation_wizard = self.env["product.creation.dynamic.wizard"].create(
            {
                "product_data": {
                    "name": "Test",
                    "purchase_ok": True,  # will be overwrite by logical value
                },
            }
        )

        action = product_creation_wizard.get_next_action()
        product = self.env["product.template"].browse(action["res_id"])
        self.assertFalse(product.purchase_ok)

    def test_prepare_step_on_custom_step_already_set_shouldnt_use_default(self):

        question = self.env["product.creation.question"].create(
            {
                "name": "purchase ok ?",
                "question": "purchase ok ?",
                "question_type": "custom",
                "sequence": 5,
            }
        )
        answer_yes = self.env["product.creation.answer"].create(
            {"question_id": question.id, "name": "Yes"}
        )
        answer_no = self.env["product.creation.answer"].create(
            {"question_id": question.id, "name": "No"}
        )
        question.default_answer_id = answer_yes
        product_creation_wizard = self.env["product.creation.dynamic.wizard"].create({})
        product_creation_wizard.write({"answer_id": answer_no.id})

        self.assertEqual(
            product_creation_wizard._prepare_product_data(),
            {},
        )


@tagged("post_install", "-at_install")
class TestProductCreationDynamicWizard(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_creation_wizard = cls.env["product.creation.dynamic.wizard"].create(
            {}
        )
        cls.product_creation_wizard.get_next_action()

    def test_wizard_data_class_serialization(self):
        wizard = Wizard()
        wizard.append(WizardStep(record_id=1, parent_index=-1, odoo_env=self.env))
        wizard.append(WizardStep(record_id=123, parent_index=2, odoo_env=self.env))

        wizard2 = Wizard.from_dict(json.loads(json.dumps(wizard.to_dict())), self.env)
        self.assertEqual(
            wizard[0].question,
            wizard2[0].question,
        )

    def test_wizard_len(self):
        wizard = Wizard()
        wizard.append(WizardStep(record_id=1, parent_index=-1, odoo_env=self.env))
        wizard.append(WizardStep(record_id=2, parent_index=2, odoo_env=self.env))
        self.assertEqual(len(wizard), 2)

    def test_product_creation_wizard(self):
        self.assertEqual(
            self.product_creation_wizard.steps[0].question,
            "What would be the product template name?",
        )

    def test_product_creation_wizard_default(self):
        product_template = self.product_creation_wizard._action_create()
        self.assertEqual(product_template.name, "Product name (created from wizard)")

    def test_flow_step0_without_record(self):
        with Form(self.product_creation_wizard) as form_step0:
            form_step0.name = "My Product name"
            wizard = form_step0.save()

        wizard.action_open_next()
        self.assertEqual(wizard.current_step, 1)
        self.assertEqual(
            wizard.steps.step_history,
            [
                0,
            ],
        )
        self.assertEqual(wizard.product_data["name"], "My Product name")

    def test_flow_consu_with_packing_auto(self):
        wizard = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        )
        wizard.write({"name": "My consu product"})
        wizard.action_open_next()
        wizard.write({"type": "consu"})
        wizard.action_open_next()
        wizard.write({"sale_ok": False})
        wizard.action_open_next()
        wizard.write({"color": 123})
        wizard.action_open_next()
        answer = self.env.ref(
            "product_creation_dynamic_wizard.product_creation_question_custom_answer_yes"
        )
        wizard.write({"answer_id": answer.id})
        action = wizard.action_open_next()
        self.assertEqual(
            wizard.product_data,
            {
                "company_id": self.env.company.id,
                "color": 123,
                "name": "My consu product",
                "type": "consu",
                "purchase_ok": "True",
                "sale_ok": False,
                "active": "True",
                "packaging_ids": [
                    [
                        0,
                        0,
                        {
                            "name": "Box 20",
                            "qty": 20,
                            "company_id": self.env.company.id,
                        },
                    ]
                ],
                "volume": 3.2,
                "weight": 3.1,
            },
        )
        self.assertEqual(action["res_model"], "product.template")
        packaging = self.env["product.template"].browse(action["res_id"]).packaging_ids
        packaging.ensure_one()
        self.assertEqual(packaging.name, "Box 20")
        self.assertEqual(packaging.qty, 20)
        self.assertEqual(packaging.company_id, self.env.company)

    def test_flow_service_product(self):
        wizard = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        )
        wizard.write({"name": "My service product"})
        wizard.action_open_next()
        self.assertEqual(wizard.step.question, "Product type?")
        with Form(wizard) as form_step_type:
            form_step_type.type = "service"
            wizard = form_step_type.save()

        wizard.action_open_next()
        self.assertEqual(wizard.step.question, "Is this product active?")
        answer = self.env.ref(
            "product_creation_dynamic_wizard.product_creation_question_custom_answer_no"
        )
        wizard.write({"answer_id": answer.id})
        self.assertEqual(wizard.steps[9].answer_id, answer.id)
        self.assertEqual(
            wizard.product_data,
            {
                "company_id": self.env.company.id,
                "name": "My service product",
                "type": "service",
                "purchase_ok": False,
                "sale_ok": "True",
            },
        )
        action = wizard.action_open_next()
        self.assertEqual(
            wizard.product_data,
            {
                "company_id": self.env.company.id,
                "name": "My service product",
                "type": "service",
                "purchase_ok": False,
                "sale_ok": "True",
                "active": False,
                "color": 987,
                "volume": 3.2,
                "weight": 3.1,
            },
        )
        self.assertEqual(action["res_model"], "product.template")

    def test_read_custom_response_on_current_step(self):
        self.product_creation_wizard.current_step = 9
        self.assertEqual(
            self.product_creation_wizard.step.question, "Is this product active?"
        )
        answer = self.env.ref(
            "product_creation_dynamic_wizard.product_creation_question_custom_answer_no"
        )
        self.product_creation_wizard.write({"answer_id": answer.id})
        read_result = self.product_creation_wizard.read(fields=["answer_id"], load="")
        self.assertEqual(
            read_result,
            [
                {
                    "id": self.product_creation_wizard.id,
                    "answer_id": (answer.id, "No"),
                }
            ],
        )

    def test_read_custom_answer_and_wizard_field(self):
        self.product_creation_wizard.current_step = 0
        self.product_creation_wizard.write(
            {
                "name": "Product test",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
        read_result = self.product_creation_wizard.read(
            fields=["name", "current_step", "sale_ok", "color"]
        )
        self.assertEqual(
            read_result,
            [
                {
                    "id": self.product_creation_wizard.id,
                    "name": "Product test",
                    "current_step": 0,
                    "sale_ok": True,
                    "color": False,
                }
            ],
        )

    def test_custom_questions(self):
        self.product_creation_wizard.current_step = 9
        self.assertEqual(
            self.product_creation_wizard.step.question, "Is this product active?"
        )
        wizard = self.env["product.creation.dynamic.wizard"].with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        )
        form_view = wizard.fields_view_get()

        doc = etree.XML(form_view["arch"])
        answer_node = None
        for node in doc.xpath(
            "//form/group[@name='question']/field[@name='answer_id']"
        ):
            answer_node = node
        self.assertIsNotNone(answer_node)
        self.assertEqual(
            answer_node.attrib.get("options"),
            "{'no_create': True, 'no_create_edit': True, 'no_open': True}",
        )
        self.assertEqual(
            answer_node.attrib.get("domain"),
            f'[("question_id", "=", {self.product_creation_wizard.step.id})]',
        )
        self.assertEqual(answer_node.get("modifiers"), '{"required": true}')

    def test_field_with_custom_view_with_default_value(self):
        self.product_creation_wizard.current_step = 5
        self.assertEqual(
            self.product_creation_wizard.step.name,
            "1.1.2 - product packaging custom view",
        )
        wizard = self.env["product.creation.dynamic.wizard"].with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        )
        form_view = wizard.fields_view_get()

        doc = etree.XML(form_view["arch"])
        packaging_node = None
        for node in doc.xpath(
            "//form/group[@name='question']/field[@name='packaging_ids']"
        ):
            packaging_node = node
        self.assertIsNotNone(packaging_node)
        self.assertEqual(
            packaging_node.attrib.get("context"),
            "{'tree_view_ref':'product.product_packaging_tree_view2',"
            " 'form_view_ref':'product.product_packaging_form_view2',"
            " 'default_name': 'Box of 10', 'default_qty': 10,"
            " 'default_company_id': current_company_id}",
        )

    def test_read_without_field(self):
        res = self.product_creation_wizard.read()
        self.assertEqual(res[0]["current_step"], 0)

    def test_fields_view_get_tree(self):
        self.product_creation_wizard.action_open_next()
        result = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        ).fields_view_get(view_type="tree")
        self.assertFalse('<field name="type"' in result["arch"])

    def test_fields_view_get_unknown_wizard_id(self):
        self.product_creation_wizard.action_open_next()
        result = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        ).fields_view_get()
        self.assertTrue('<field name="type"' in result["arch"], result["arch"])
        result = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name, active_id=-666
        ).fields_view_get()
        self.assertTrue('<field name="name"' in result["arch"])

    def test_ignore_untraversed_tree(self):
        self.product_creation_wizard.write({"name": "My service product"})
        self.product_creation_wizard.action_open_next()
        self.product_creation_wizard.write({"type": "service"})
        self.product_creation_wizard.action_open_next()
        self.assertEqual(
            [
                self.product_creation_wizard.steps[i].question
                for i in self.product_creation_wizard.steps.step_history
            ],
            [
                "What would be the product template name?",
                "Product type?",
                "automatic step: purchase ok",
                "automatic step: sale ok",
            ],
        )

    def test_action_open_previous_back_to_previous_non_automatic_step(self):
        self.product_creation_wizard.write({"name": "My service product"})
        self.product_creation_wizard.action_open_next()
        self.product_creation_wizard.write({"type": "consu"})
        self.product_creation_wizard.action_open_next()

        self.assertEqual(self.product_creation_wizard.steps.step_history, [0, 1, 2])
        self.product_creation_wizard.action_open_previous()
        self.assertEqual(
            self.product_creation_wizard.steps.step_history,
            [
                0,
            ],
        )
        self.assertEqual(self.product_creation_wizard.current_step, 1)

    def test_action_open_previous_no_history(self):
        self.assertEqual(self.product_creation_wizard.current_step, 0)
        self.product_creation_wizard.action_open_previous()
        self.assertEqual(self.product_creation_wizard.current_step, 0)


@tagged("post_install", "-at_install")
class TestProductCreationDynamicWizardWithProductAttributeStep(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        loader = FakeModelLoader(cls.env, cls.__module__)
        cls.addClassCleanup(loader.restore_registry)
        loader.backup_registry()
        from .fake_product import FakeProduct

        loader.update_registry((FakeProduct,))
        cls.env["product.creation.question"].create(
            {
                "name": "Product variant list",
                "sequence": 4,
                "field_id": cls.env["ir.model.fields"]
                .search(
                    [
                        ("model", "=", "product.template"),
                        ("name", "=", "attribute_line_ids"),
                    ]
                )
                .id,
                "default_field_value": (
                    '[[0, 0, {"attribute_id":'
                    + str(cls.env.ref("product.product_attribute_2").id)
                    + ' , "value_ids": [[6, 0, '
                    + str(
                        (
                            cls.env.ref("product.product_attribute_value_3")
                            | cls.env.ref("product.product_attribute_value_4")
                        ).ids
                    )
                    + "]]}]]"
                ),
                "is_automatic": True,
            }
        )
        cls.env["product.creation.question"].create(
            {
                "name": "Product attribute",
                "question": "What's the product attribute value ?",
                "field_id": cls.env["ir.model.fields"]
                .search(
                    [
                        ("model", "=", "product.product"),
                        ("name", "=", "product_attribute"),
                    ]
                )
                .id,
                "sequence": 5,
            }
        )

        cls.product_creation_wizard = cls.env["product.creation.dynamic.wizard"].create(
            {}
        )
        cls.product_creation_wizard.get_next_action()

    def test_flow_with_product(self):
        wizard = self.product_creation_wizard.with_context(
            active_model=self.product_creation_wizard._name,
            active_id=self.product_creation_wizard.id,
        )
        wizard.write({"name": "My consu product"})
        wizard.action_open_next()
        wizard.write({"type": "consu"})
        wizard.action_open_next()
        wizard.write({"sale_ok": False})
        wizard.action_open_next()
        wizard.write({"color": 123})
        wizard.action_open_next()
        answer = self.env.ref(
            "product_creation_dynamic_wizard.product_creation_question_custom_answer_yes"
        )
        wizard.write({"answer_id": answer.id})
        wizard.action_open_next()

        wizard.write({"product_attribute": "joe"})
        action = wizard.action_open_next()
        product_template = self.env["product.template"].browse(action["res_id"])
        self.assertEqual(
            product_template.product_variant_ids.mapped("product_attribute"),
            ["joe", "joe"],
        )
