import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-odoo-pim",
    description="Meta package for oca-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-attribute_set',
        'odoo14-addon-attribute_set_completeness',
        'odoo14-addon-attribute_set_mass_edit',
        'odoo14-addon-attribute_set_searchable',
        'odoo14-addon-pim',
        'odoo14-addon-product_attribute_set',
        'odoo14-addon-product_attribute_set_completeness',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
