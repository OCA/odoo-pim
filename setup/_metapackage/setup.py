import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-odoo-pim",
    description="Meta package for oca-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-attribute_set>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
