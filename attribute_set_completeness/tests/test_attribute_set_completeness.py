# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestAttributeSetCompleteness(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        vals = {
            "nature": "custom",
            "model_id": cls.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test",
            "name": "x_test",
            "attribute_group_id": cls.group.id,
        }
        cls.attr1 = cls.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test2", "field_description": "Attribute test2"})
        cls.attr2 = cls.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test3", "field_description": "Attribute test3"})
        cls.attr3 = cls.env["attribute.attribute"].create(vals)

        vals = {
            "name": "My attribute Set",
            "model_id": cls.model_id,
            "attribute_ids": [Command.link(cls.attr1.id), Command.link(cls.attr2.id)],
            "attribute_set_completeness_ids": [
                Command.create(
                    {"field_id": cls.attr1.field_id.id, "completion_rate": 50.0}
                ),
                Command.create(
                    {"field_id": cls.attr2.field_id.id, "completion_rate": 50.0}
                ),
            ],
        }
        cls.attr_set = cls.env["attribute.set"].create(vals)
        cls.rule1, cls.rule2 = cls.attr_set.attribute_set_completeness_ids

    def test_completion_rate_constrains_create(self):
        vals = {
            "name": "My attribute Set Test",
            "model_id": self.model_id,
            "attribute_ids": [
                Command.link(self.attr1.id),
                Command.link(self.attr2.id),
            ],
            "attribute_set_completeness_ids": [
                Command.create(
                    {"field_id": self.attr1.field_id.id, "completion_rate": 50.0}
                ),
                Command.create(
                    {"field_id": self.attr2.field_id.id, "completion_rate": 10.0}
                ),
            ],
        }
        error_msg = "Total of completion rate must be 100 %"
        with self.assertRaisesRegex(ValidationError, error_msg):
            self.env["attribute.set"].create(vals)

    def test_completion_rate_constrains_write_low(self):
        vals = {
            "attribute_set_completeness_ids": [
                Command.delete(self.rule1.id),
                Command.create(
                    {"field_id": self.attr1.field_id.id, "completion_rate": 10.0}
                ),
            ]
        }
        error_msg = "Total of completion rate must be 100 %"
        with self.assertRaisesRegex(ValidationError, error_msg):
            self.attr_set.write(vals)

    def test_completion_rate_constrains_write_high(self):
        vals = {
            "attribute_set_completeness_ids": [
                Command.delete(self.rule1.id),
                Command.create(
                    {"field_id": self.attr1.field_id.id, "completion_rate": 200.0}
                ),
            ]
        }
        error_msg = "Total of completion rate must be 100 %"
        with self.assertRaisesRegex(ValidationError, error_msg):
            self.attr_set.write(vals)

    def test_completion_rate_constrains_rounding(self):
        self.attr_set.write(
            {
                "attribute_ids": [Command.link(self.attr3.id)],
                "attribute_set_completeness_ids": [
                    Command.update(self.rule1.id, {"completion_rate": 33.33}),
                    Command.update(self.rule2.id, {"completion_rate": 33.33}),
                    Command.create(
                        {"field_id": self.attr3.field_id.id, "completion_rate": 33.34}
                    ),
                ],
            }
        )
        self.assertEqual(len(self.attr_set.attribute_set_completeness_ids), 3)

    def test_available_fields(self):
        self.assertEqual(
            self.rule1.available_field_ids,
            self.env["ir.model.fields"],
            "All the attributes of the set are already used",
        )
        self.attr_set.attribute_ids = [Command.link(self.attr3.id)]
        self.assertEqual(self.rule1.available_field_ids, self.attr3.field_id)

    def test_available_fields_inherited(self):
        child_set = self.env["attribute.set"].create(
            {
                "name": "Child Set",
                "model_id": self.model_id,
                "parent_id": self.attr_set.id,
                "attribute_ids": [Command.link(self.attr3.id)],
                "attribute_set_completeness_ids": [
                    Command.create(
                        {"field_id": self.attr3.field_id.id, "completion_rate": 100.0}
                    ),
                ],
            }
        )
        self.assertEqual(
            child_set.attribute_set_completeness_ids.available_field_ids,
            self.attr1.field_id | self.attr2.field_id,
        )

    def test_completion_rate(self):
        # Case 1: Create the partner
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.assertFalse(partner.attribute_set_completion_state)
        self.assertEqual(partner.attribute_set_completion_rate, 0.0)
        # Case 2: Set an attribute set
        partner.write({"attribute_set_id": self.attr_set.id})
        self.assertEqual(partner.attribute_set_completion_state, "not_complete")
        self.assertEqual(partner.attribute_set_completion_rate, 0.0)
        self.assertEqual(
            partner.attribute_set_not_completed_ids, self.rule1 | self.rule2
        )
        # Case 3: Set a field (50% completion)
        partner.write({"x_test": "test"})
        self.assertEqual(partner.attribute_set_completion_state, "not_complete")
        self.assertEqual(partner.attribute_set_completion_rate, 50.0)
        self.assertEqual(partner.attribute_set_completed_ids, self.rule1)
        self.assertEqual(partner.attribute_set_not_completed_ids, self.rule2)
        # Case 4: Set another field (100% completion)
        partner.write({"x_test2": "test"})
        self.assertEqual(partner.attribute_set_completion_state, "complete")
        self.assertEqual(partner.attribute_set_completion_rate, 100.0)
        self.assertFalse(partner.attribute_set_not_completed_ids)
        # Case 5: Unset a field
        partner.write({"x_test": False})
        self.assertEqual(partner.attribute_set_completion_state, "not_complete")
        self.assertEqual(partner.attribute_set_completion_rate, 50.0)

    def test_completion_rate_on_create(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "attribute_set_id": self.attr_set.id,
                "x_test": "a",
            }
        )
        self.assertEqual(partner.attribute_set_completion_rate, 50.0)

    def test_completion_rate_stored(self):
        partner = self.env["res.partner"].create(
            {"name": "Test Partner", "attribute_set_id": self.attr_set.id}
        )
        partner.write({"x_test": "test", "x_test2": "test"})
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(
            self.env["res.partner"].search(
                [
                    ("id", "=", partner.id),
                    ("attribute_set_completion_state", "=", "complete"),
                ]
            ),
            partner,
        )

    def test_completion_rate_config_change(self):
        partner = self.env["res.partner"].create(
            {"name": "Test Partner", "attribute_set_id": self.attr_set.id}
        )
        partner.write({"x_test": "test"})
        self.assertEqual(partner.attribute_set_completion_rate, 50.0)
        self.attr_set.write(
            {
                "attribute_set_completeness_ids": [
                    Command.update(self.rule1.id, {"completion_rate": 80.0}),
                    Command.update(self.rule2.id, {"completion_rate": 20.0}),
                ]
            }
        )
        self.assertEqual(partner.attribute_set_completion_rate, 80.0)
