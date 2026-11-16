# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import TestProductSimilarityCommon


class TestFieldVectorizationWizard(TestProductSimilarityCommon):
    def _run_wizard(self, field, weight=1):
        wizard = self.Wizard.create({"field_id": field.id, "weight": weight})
        return wizard.put_in_vector_action()

    def test_wizard_vectorize_boolean_field(self):
        action = self._run_wizard(self.boolean_field, weight=2)
        characteristics = self.Characteristic.search([])
        self.assertEqual(len(characteristics), 1)
        self.assertEqual(characteristics.weight, 2)
        self.assertEqual(action["tag"], "display_notification")
        # Running it again does not create duplicates
        self._run_wizard(self.boolean_field)
        self.assertEqual(self.Characteristic.search_count([]), 1)

    def test_wizard_vectorize_selection_field(self):
        self._run_wizard(self.selection_field)
        self.assertEqual(
            self.Characteristic.search_count([]), len(self.selection_field_values)
        )

    def test_wizard_vectorize_related_selection_field(self):
        self._run_wizard(self.related_selection_field)
        template_field = self.env["ir.model.fields"]._get("product.template", "type")
        self.assertTrue(template_field.selection_ids)
        self.assertEqual(
            self.Characteristic.search_count([]), len(template_field.selection_ids)
        )

    def test_wizard_nothing_to_create(self):
        self._run_wizard(self.boolean_field)
        action = self._run_wizard(self.boolean_field)
        self.assertEqual(action["params"]["type"], "warning")

    def test_wizard_vectorize_many_to_one_field(self):
        self._run_wizard(self.many_to_one_field)
        self.assertEqual(
            self.Characteristic.search_count([]), len(self.many_to_one_field_values)
        )

    def test_wizard_vectorize_many_to_many_field(self):
        self._run_wizard(self.many_to_many_field)
        characteristics = self.Characteristic.search([])
        self.assertEqual(len(characteristics), len(self.many_to_many_field_values))
        self.assertEqual(
            characteristics.mapped("vector_index"), list(range(len(characteristics)))
        )

    def test_wizard_only_adds_missing_values(self):
        value_ids = list(self.many_to_many_field_values)
        self.Characteristic.create(
            {"field_id": self.many_to_many_field.id, "value_id": value_ids[0]}
        )
        action = self._run_wizard(self.many_to_many_field)
        self.assertEqual(
            self.Characteristic.search_count([]), len(self.many_to_many_field_values)
        )
        self.assertIn(str(len(value_ids) - 1), action["params"]["message"])
