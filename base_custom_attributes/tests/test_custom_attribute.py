# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestCustomAttribute(common.TransactionCase):

    def setUp(self):

        super(TestCustomAttribute, self).setUp()

        self.attribute_model = self.env['attribute.attribute']
        self.set_model = self.env['attribute.set']
        self.group_model = self.env['attribute.group']
        self.location_model = self.env['attribute.location']
        self.option_model = self.env['attribute.option']
        self.wizard_model = self.env['attribute.option.wizard']
        self.model_model = self.env['ir.model']
        self.field_model = self.env['ir.model.fields']

        self.model = self.env['ir.model'].search([
            ('model', '=', 'x_test_model_1')])
        if not self.model:
            self.model = self.env['ir.model'].create({
                'name': 'test_model_1',
                'model': 'x_test_model_1'
            })

        self.set_1 = self.set_model.create({
            'name': 'Set 1',
            'model_id': self.model.id,
        })

        self.set_2 = self.set_model.create({
            'name': 'Set 2',
            'model_id': self.model.id,
        })

        self.group_1 = self.group_model.create({
            'name': 'Group 1',
            'attribute_set_id': self.set_1.id,
            'model_id': self.model.id,
        })

        self.vals = {
            'field_description': 'Attribute 1',
            'name': 'x_attribute_1',
            'attribute_type': 'char',
            'model_id': self.model.id,
        }

    def test_create_attribute_char(self):
        self.vals.update({
            'attribute_type': 'char',
            'name': 'x_attribute_char',
            })
        attribute = self.attribute_model.create(self.vals)

        self.assertEqual(attribute.ttype, 'char')

    def test_create_attribute_selection(self):
        self.vals.update({
            'name': 'x_attribute_selection',
            'attribute_type': 'select',
            'option_ids': [
                (0, 0, {
                    'name': 'Value 1',
                }),
                (0, 0, {
                    'name': 'Value 2',
                }),
            ]
        })
        attribute = self.attribute_model.create(self.vals)

        self.assertEqual(attribute.ttype, 'many2one')
        self.assertEqual(attribute.relation, 'attribute.option')

    def test_create_attribute_multiselect(self):
        self.vals.update({
            'attribute_type': 'multiselect',
            'name': 'x_attribute_mutliselect',
            'option_ids': [
                (0, 0, {
                    'name': 'Value 1',
                }),
                (0, 0, {
                    'name': 'Value 2',
                }),
            ]
        })
        attribute = self.attribute_model.create(self.vals)

        self.assertEqual(attribute.ttype, 'many2many')
        self.assertEqual(attribute.relation, 'attribute.option')

#    def test_wizard(self):
#        sequence_type_model = self.env['res.partner.category']
#        sequence_type = sequence_type_model.create({
#            'name': 'Sequence type 1',
#        })
#        model = self.model_model.search([
#           ('name', '=', 'res.partner.category')])
#
#        self.vals.update({
#            'attribute_type': 'multiselect',
#            'name': 'x_attribute_multiselect_2',
#            'relation_model_id': model.id,
#        })
#
#        attribute = self.attribute_model.create(self.vals)
#
#        self.wizard_model.create({
#            'attribute_id': attribute.id,
#            'option_ids': [(6, 0, [sequence_type.id])]
#        })
#
#        attribute.refresh()
#
#        self.assertEqual(len(attribute.option_ids), 1)
#        option = attribute.option_ids[0]
#        self.assertEqual(option.value_ref, sequence_type)
