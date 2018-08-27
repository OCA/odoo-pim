# -*- coding: utf-8 -*-

{
    'name': 'base_custom_attributes',
    'version': '10.0.0.0.1',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'author': "Akretion",
    'website': 'https://akretion.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/attribute_security.xml',
        'views/menu_view.xml',
        'views/attribute_attribute_view.xml',
        'views/attribute_group_view.xml',
        'views/attribute_option_view.xml',
        'views/attribute_set_view.xml',
        'wizard/attribute_option_wizard_view.xml',
    ],
    'demo': [
        'demo/attribute.xml',
    ],
    'external_dependencies': {
        'python': ['unidecode'],
    }
}
