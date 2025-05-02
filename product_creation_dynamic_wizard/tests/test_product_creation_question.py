from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestProductCreationQuestion(SavepointCase):
    def test_product_creation_question_complete_name(self):
        self.assertEqual(
            self.env.ref(
                "product_creation_dynamic_wizard."
                "product_creation_question_sale_consu"
            ).complete_name,
            "1 Product type / 1.1 Sale consumable product",
        )
        self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_category"
        ).name = "Test"
        self.assertEqual(
            self.env.ref(
                "product_creation_dynamic_wizard."
                "product_creation_question_sale_consu"
            ).complete_name,
            "Test / 1.1 Sale consumable product",
        )

    def test_conditional_question_remove_parent(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_sale_consu"
        )
        question.parent_id = False
        self.assertFalse(question.conditional_question)

    def test_conditional_question_set_change_parent_id(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_sale_consu"
        )
        question.parent_id = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_name"
        )
        self.assertTrue(question.conditional_question)

    def test_conditional_question_parent_becomes_logical(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_sale_consu"
        )
        question.parent_id.question_type = "logical"
        self.assertFalse(question.conditional_question)

    def test_is_automatic_question_type_logical(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_custom"
        )
        self.assertFalse(question.is_automatic)
        question.question_type = "logical"
        self.assertTrue(question.is_automatic)

    def test_is_automatic_question_type_field(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard." "product_creation_question_custom"
        )
        self.assertFalse(question.is_automatic)
        question.question_type = "field"
        self.assertFalse(question.is_automatic)

    def test_validate_custom_view(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_sale_consu_packaging_custom_view"
        )
        with self.assertRaisesRegex(ValidationError, r"Incorrect XML data"):
            question.custom_view = "<div></wrongdiv>"

    def test_validate_logical_default_values(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        with self.assertRaisesRegex(ValidationError, r"Incorrect JSON data"):
            question.logical_default_values = '{"test": "trailing coma",}'

    def test_validate_logical_values(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        with self.assertRaisesRegex(ValidationError, r"Incorrect JSON data"):
            question.logical_values = '{"missing": "close bracket"'

    def test_validate_custom_view_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_sale_consu_packaging_custom_view"
        )
        question.custom_view = "<div></div>"

    def test_validate_logical_default_values_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        question.logical_default_values = '{"test": "trailing coma"}'

    def test_validate_logical_values_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        question.logical_values = (
            '{"missing": "close bracket",'
            ' "test_id": {"company_id": current_company_id}}'
        )

    def test_validate_custom_view_false_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_sale_consu_packaging_custom_view"
        )
        question.custom_view = False

    def test_validate_logical_default_values_false_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        question.logical_default_values = False

    def test_validate_logical_values_false_ok(self):
        question = self.env.ref(
            "product_creation_dynamic_wizard."
            "product_creation_question_logical_values"
        )
        question.logical_values = False
