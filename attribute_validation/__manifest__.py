{
    "name": "Attribute Validation",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Data validation for dynamic attributes without Many2one relations",
    "author": "OBS Solutions B.V., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "development_status": "Beta",
    "maintainers": ["bosd"],
    "license": "AGPL-3",
    "depends": [
        "base",
        "product_attribute_set",
    ],
    "data": [
        "security/attribute_validation_security.xml",
        "security/ir.model.access.csv",
        "views/attribute_validation_rule_views.xml",
        "views/attribute_attribute_views.xml",
        "data/validation_rule_templates.xml",
    ],
    "demo": [
        "demo/attribute_validation_demo.xml",
    ],
    "installable": True,
    "auto_install": False,
}
