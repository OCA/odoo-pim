import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-odoo-pim",
    description="Meta package for oca-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-attribute_set',
        'odoo12-addon-attribute_set_completeness',
        'odoo12-addon-attribute_set_mass_edit',
        'odoo12-addon-attribute_set_searchable',
        'odoo12-addon-pim',
        'odoo12-addon-product_attribute_set',
        'odoo12-addon-product_attribute_set_completeness',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
