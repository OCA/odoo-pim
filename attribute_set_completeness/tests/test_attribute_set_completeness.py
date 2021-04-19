# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import ValidationError

from odoo.addons.component.tests.common import SavepointComponentCase


class TestAttributeSetCompleteness(SavepointComponentCase):
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

        cls.loader.update_registry([ResPartner])

        from .res_partner_event_listener import ResPartnerEventListener  # noqa: F401

        ResPartnerEventListener._build_component(cls._components_registry)

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(TestAttributeSetCompleteness, cls).tearDownClass()

    def test_completion_rate_constrains_create(self):
        vals = {
            "name": "My attribute Set Test",
            "is_automatic_rate": False,
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
            "is_automatic_rate": False,
            "attribute_set_completeness_ids": [
                (2, completion_rules[0].id),
                (0, 0, {"field_id": self.attr1.field_id.id, "completion_rate": 10.0}),
            ],
        }

        with self.assertRaises(ValidationError):
            self.attr_set.write(vals)

    def test_completion_rate_constrains_write_high(self):
        completion_rules = self.attr_set.attribute_set_completeness_ids
        vals = {
            "is_automatic_rate": False,
            "attribute_set_completeness_ids": [
                (2, completion_rules[0].id),
                (0, 0, {"field_id": self.attr1.field_id.id, "completion_rate": 200.0},),
            ],
        }

        with self.assertRaises(ValidationError):
            self.attr_set.write(vals)

    def test_completion_rate(self):
        vals = {
            "name": "Test Partner",
        }
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

    def test_auto_completion_rate(self):
        #  test with "is_automatic_rate" == True by default
        vals = {
            "nature": "custom",
            "model_id": self.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test3",
            "name": "x_test3",
            "attribute_group_id": self.group.id,
        }
        self.attr3 = self.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test4", "field_description": "Attribute test4"})
        self.attr4 = self.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test5", "field_description": "Attribute test5"})
        self.attr5 = self.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test6", "field_description": "Attribute test6"})
        self.attr6 = self.env["attribute.attribute"].create(vals)

        vals = {
            "name": "My attribute Set 2",
            "model_id": self.model_id,
            "attribute_ids": [
                (4, self.attr3.id),
                (4, self.attr4.id),
                (4, self.attr5.id),
                (4, self.attr6.id),
            ],
            "attribute_set_completeness_ids": [
                (0, 0, {"field_id": self.attr3.field_id.id, "completion_rate": 25.0}),
                (0, 0, {"field_id": self.attr4.field_id.id, "completion_rate": 60.0}),
                (0, 0, {"field_id": self.attr5.field_id.id, "completion_rate": 8.0}),
                (0, 0, {"field_id": self.attr6.field_id.id, "completion_rate": 156.0}),
            ],
        }
        self.attr_set2 = self.env["attribute.set"].create(vals)

        partner2 = self.env["res.partner"].create({"name": "Test Partner 2"})

        partner2.write({"attribute_set_id": self.attr_set2.id})
        partner2.write({"x_test3": "test"})
        partner2.write({"x_test4": "test"})
        partner2.write({"x_test5": "test"})
        partner2.write({"x_test6": "test"})

        # Completion rate = 100 and complete
        self.assertEqual(partner2.completion_state, "complete")
        self.assertEqual(partner2.completion_rate, 100.0)

        # Same completion rate for each attribute (100/4 = 25)
        self.assertEqual(len(partner2.attribute_set_completeneness_ids), 4)
        self.assertEqual(
            partner2.attribute_set_completeneness_ids[0].completion_rate, 25.0
        )
        self.assertEqual(
            partner2.attribute_set_completeneness_ids[1].completion_rate, 25.0
        )
        self.assertEqual(
            partner2.attribute_set_completeneness_ids[2].completion_rate, 25.0
        )
        self.assertEqual(
            partner2.attribute_set_completeneness_ids[3].completion_rate, 25.0
        )

    def test_auto_completion_rate_with_3_attributes(self):
        # With "is_automatic_rate" == True by default
        # Sometimes, the total completion_rate divides by the attributes number
        # can not let equal completion_rates for each attribute and gives a remainder.
        # For example : 100 / 3 = 33.33333333333...
        # This remainder will be added to the first attribute when saving the set.

        vals = {
            "nature": "custom",
            "model_id": self.model_id,
            "attribute_type": "char",
            "field_description": "Attribute test3",
            "name": "x_test3",
            "attribute_group_id": self.group.id,
        }
        self.attr3 = self.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test4", "field_description": "Attribute test4"})
        self.attr4 = self.env["attribute.attribute"].create(vals)

        vals.update({"name": "x_test5", "field_description": "Attribute test5"})
        self.attr5 = self.env["attribute.attribute"].create(vals)

        vals = {
            "name": "My attribute Set 3",
            # "is_automatic_rate": True,
            "model_id": self.model_id,
            "attribute_ids": [
                (4, self.attr3.id),
                (4, self.attr4.id),
                (4, self.attr5.id),
            ],
            "attribute_set_completeness_ids": [
                (0, 0, {"field_id": self.attr3.field_id.id, "completion_rate": 20.0}),
                (0, 0, {"field_id": self.attr4.field_id.id, "completion_rate": 60.0}),
                (0, 0, {"field_id": self.attr5.field_id.id, "completion_rate": 30.0}),
            ],
        }
        self.attr_set3 = self.env["attribute.set"].create(vals)

        partner3 = self.env["res.partner"].create({"name": "Test Partner 3"})

        partner3.write({"attribute_set_id": self.attr_set3.id})
        partner3.write({"x_test3": "test"})
        partner3.write({"x_test4": "test"})
        partner3.write({"x_test5": "test"})

        # Completion rate = 100 and complete
        self.assertEqual(partner3.completion_state, "complete")
        self.assertEqual(partner3.completion_rate, 100.0)

        # 3 attributes give 33 % of completion rate with 1 as remainder.
        # The remainder will be added to the first attribute when saving the set.
        self.assertEqual(
            partner3.attribute_set_completeneness_ids[0].completion_rate, 34.0
        )
        self.assertEqual(
            partner3.attribute_set_completeneness_ids[1].completion_rate,
            partner3.attribute_set_completeneness_ids[2].completion_rate,
        )
