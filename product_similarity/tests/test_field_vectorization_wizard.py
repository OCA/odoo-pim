# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import TestProductSimilarityCommon


class TestProductVectorCharacteristic(TestProductSimilarityCommon):
    def test_wizard_vectorize_biary_field(self):
        wizard_action = self.env[
            "product.vector.characteristic"
        ].field_vectorization_wizard_action()
        wizard = self.env[wizard_action["res_model"]].create(
            {"field_id": self.boolean_field.id}
        )
        wizard.put_in_vector_action()

        characteristic = self.env["product.vector.characteristic"].search([])
        self.assertEqual(
            len(characteristic),
            1,
            "Expected exactly one characteristic to be created by wizard for binary field.",
        )

    def test_wizard_vectorize_selection_field(self):
        wizard_action = self.env[
            "product.vector.characteristic"
        ].field_vectorization_wizard_action()
        wizard = self.env[wizard_action["res_model"]].create(
            {"field_id": self.selection_field.id}
        )
        wizard.put_in_vector_action()

        characteristic = self.env["product.vector.characteristic"].search([])
        self.assertEqual(
            len(characteristic),
            len(self.selection_field_values),
        )

    def test_wizard_vectorize_many_to_one_field(self):
        wizard_action = self.env[
            "product.vector.characteristic"
        ].field_vectorization_wizard_action()
        wizard = self.env[wizard_action["res_model"]].create(
            {"field_id": self.many_to_one_field.id}
        )
        wizard.put_in_vector_action()

        characteristic = self.env["product.vector.characteristic"].search([])
        self.assertEqual(
            len(characteristic),
            len(self.many_to_one_field_values),
        )

    def test_wizard_vectorize_many_to_many_field(self):
        wizard_action = self.env[
            "product.vector.characteristic"
        ].field_vectorization_wizard_action()
        wizard = self.env[wizard_action["res_model"]].create(
            {"field_id": self.many_to_many_field.id}
        )
        wizard.put_in_vector_action()

        characteristic = self.env["product.vector.characteristic"].search([])
        self.assertEqual(
            len(characteristic),
            len(self.many_to_many_field_values),
        )
