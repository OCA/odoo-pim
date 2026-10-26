# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import common


class TestAttributeSet(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_id = cls.env.ref("base.model_res_partner").id
        cls.group = cls.env["attribute.group"].create(
            {"name": "My Group", "model_id": cls.model_id}
        )
        # Do not commit
        cls.env.cr.commit = mock.Mock()

    def _create_attribute(self, vals):
        vals.update(
            {
                "nature": "custom",
                "model_id": self.model_id,
                "field_description": "Attribute {key}".format(
                    key=vals["attribute_type"]
                ),
                "name": "x_{key}".format(key=vals["attribute_type"]),
                "attribute_group_id": self.group.id,
            }
        )
        return self.env["attribute.attribute"].create(vals)

    def test_create_attribute_char(self):
        attribute = self._create_attribute({"attribute_type": "char"})
        self.assertEqual(attribute.ttype, "char")

    def test_create_attribute_selection(self):
        attribute = self._create_attribute(
            {
                "attribute_type": "select",
                "option_ids": [
                    (0, 0, {"name": "Value 1"}),
                    (0, 0, {"name": "Value 2"}),
                ],
            }
        )

        self.assertEqual(attribute.ttype, "many2one")
        self.assertEqual(attribute.relation, "attribute.option")

    def test_create_attribute_multiselect(self):
        attribute = self._create_attribute(
            {
                "attribute_type": "multiselect",
                "option_ids": [
                    (0, 0, {"name": "Value 1"}),
                    (0, 0, {"name": "Value 2"}),
                ],
            }
        )

        self.assertEqual(attribute.ttype, "many2many")
        self.assertEqual(attribute.relation, "attribute.option")

    def test_wizard_validate(self):
        model_id = self.env["ir.model"].search([("model", "=", "res.partner")])
        attribute = self._create_attribute(
            {
                "attribute_type": "select",
                "option_ids": [
                    (0, 0, {"name": "Value 1"}),
                    (0, 0, {"name": "Value 2"}),
                ],
                "relation_model_id": model_id.id,
            }
        )
        PartnerModel = self.env["res.partner"]
        partner = PartnerModel.create({"name": "John Doe"})
        vals = {
            "attribute_id": attribute.id,
            "option_ids": [[4, partner.id]],
        }
        OptionWizard = self.env["attribute.option.wizard"]
        # attribute has only two options
        len_2 = len(attribute.option_ids)
        self.assertTrue(len_2 == 2)
        # a new option should be created
        wizard1 = OptionWizard.create(vals)
        len_3 = len(attribute.option_ids)
        self.assertTrue(len_3 > 2)
        self.assertIn(partner.name, attribute.option_ids.mapped("name"))
        vals = {
            "attribute_id": attribute.id,
        }
        # no option should be created
        # as option_ids key is not passed in vals
        wizard2 = OptionWizard.create(vals)
        len_default = len(attribute.option_ids)
        self.assertTrue(wizard1 != wizard2)
        self.assertEqual(len_default, len_3)
