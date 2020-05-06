import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-shopinvader-odoo-pim",
    description="Meta package for shopinvader-odoo-pim Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-base_custom_attribute',
        'odoo10-addon-pim_custom_attribute',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
