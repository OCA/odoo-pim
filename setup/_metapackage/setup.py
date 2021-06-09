import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-odoo-pim",
    description="Meta package for oca-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-attribute_set',
        'odoo13-addon-attribute_set_completeness',
        'odoo13-addon-attribute_set_mass_edit',
        'odoo13-addon-attribute_set_searchable',
        'odoo13-addon-pim',
        'odoo13-addon-product_attribute_set',
        'odoo13-addon-product_attribute_set_completeness',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
