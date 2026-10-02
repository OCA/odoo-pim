{
    "name": "Attribute Set JSONB",
    "version": "19.0.1.0.0",
    "category": "Technical",
    "summary": "JSONB optimization and expression indexing for attribute_set",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "license": "AGPL-3",
    "depends": [
        "attribute_set",
        "base_sparse_field_jsonb",
    ],
    "data": [
        "views/attribute_attribute_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": True,
}
