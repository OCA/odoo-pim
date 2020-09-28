# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase

try:
    from odoo_test_helper import FakeModelLoader
except ImportError:
    FakeModelLoader = None


class TestAttributeSetCompleteness(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAttributeSetCompleteness, cls).setUpClass()
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

        vals = {
            "name": "My attribute Set",
            "model_id": cls.model_id,
            "attribute_ids": [(4, cls.attr1.id), (4, cls.attr2.id)],
            "attribute_set_completeness_ids": [
                (0, 0, {"field_id": cls.attr1.field_id.id, "completion_rate": 50.0}),
                (0, 0, {"field_id": cls.attr2.field_id.id, "completion_rate": 50.0}),
            ],
        }
        cls.attr_set = cls.env["attribute.set"].create(vals)
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from odoo.addons.attribute_set.tests.models import ResPartner
        from .res_partner_event_listener import ResPartnerEventListener  # noqa: F401

        cls.component_builder = cls.env["component.builder"]
        cls.component_builder._register_hook()
        cls.component_builder.load_components("attribute_set_completeness")
        cls.loader.update_registry((ResPartner,))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(TestAttributeSetCompleteness, cls).tearDownClass()

    def test_completion_rate_constrains_create(self):
        vals = {
            "name": "My attribute Set Test",
            "model_id": self.model_id,
            "attribute_ids": [(4, self.attr1.id), (4, self.attr2.id)],
            "attribute_set_completeness_ids": [
                (0, 0, {"field_id": self.attr1.field_id.id, "completion_rate": 50.0}),
                (0, 0, {"field_id": self.attr2.field_id.id, "completion_rate": 10.0}),
            ],
        }
        with self.assertRaises(ValidationError):
            self.env["attribute.set"].create(vals)

    def test_completion_rate_constrains_write_low(self):
        completion_rules = self.attr_set.attribute_set_completeness_ids
        vals = {
            "attribute_set_completeness_ids": [
                (2, completion_rules[0].id),
                (0, 0, {"field_id": self.attr1.field_id.id, "completion_rate": 10.0}),
            ]
        }

        with self.assertRaises(ValidationError):
            self.attr_set.write(vals)

    def test_completion_rate_constrains_write_high(self):
        completion_rules = self.attr_set.attribute_set_completeness_ids
        vals = {
            "attribute_set_completeness_ids": [
                (2, completion_rules[0].id),
                (0, 0, {"field_id": self.attr1.field_id.id, "completion_rate": 200.0},),
            ]
        }

        with self.assertRaises(ValidationError):
            self.attr_set.write(vals)

    def test_completion_rate(self):
        vals = {"name": "Test Partner"}
        partner = self.env["res.partner"].create(vals)
        self.assertEqual(partner.completion_state, "not_complete")
        self.assertEqual(partner.completion_rate, 0.0)

        partner.write({"attribute_set_id": self.attr_set.id})
        partner.invalidate_cache()
        self.assertEqual(partner.completion_state, "not_complete")
        self.assertEqual(partner.completion_rate, 0.0)

        partner.write({"x_test": "test"})
        partner.invalidate_cache()
        self.assertEqual(partner.completion_state, "not_complete")
        self.assertEqual(partner.completion_rate, 50.0)

        partner.write({"x_test2": "test"})
        partner.invalidate_cache()
        self.assertEqual(partner.completion_state, "complete")
        self.assertEqual(partner.completion_rate, 100.0)
