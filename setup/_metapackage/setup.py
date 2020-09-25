import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-shopinvader-odoo-pim",
    description="Meta package for shopinvader-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-attribute_set',
        'odoo13-addon-product_attribute_set',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
