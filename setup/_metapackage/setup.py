import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-shopinvader-odoo-pim",
    description="Meta package for shopinvader-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-attribute_set',
        'odoo12-addon-pim',
        'odoo12-addon-product_attribute_set',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
