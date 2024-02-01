import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-odoo-pim",
    description="Meta package for oca-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-attribute_set>=16.0dev,<16.1dev',
        'odoo-addon-product_attribute_set>=16.0dev,<16.1dev',
        'odoo-addon-product_search_multi_value>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
