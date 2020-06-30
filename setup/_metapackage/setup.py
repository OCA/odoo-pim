import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-shopinvader-odoo-pim",
    description="Meta package for shopinvader-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-attribute_set',
        'odoo10-addon-attribute_set_completeness',
        'odoo10-addon-attribute_set_mass_edit',
        'odoo10-addon-attribute_set_searchable',
        'odoo10-addon-pim',
        'odoo10-addon-product_attribute_set',
        'odoo10-addon-product_attribute_set_completeness',
        'odoo10-addon-product_search_multi_value',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
