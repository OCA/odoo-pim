{
    "name": "Website Attribute Set JSONB",
    "version": "19.0.1.0.1",
    "category": "Website/Website",
    "summary": "Website shop filtering for JSONB serialized attributes",
    "author": "OBS Solutions B.V., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/odoo-pim",
    "license": "AGPL-3",
    "depends": [
        "website_sale",
        "website_attribute_set",
        "attribute_set_jsonb",
        "attribute_set_jsonb_index",
    ],
    "data": [
        "views/attribute_attribute_views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_attribute_set_jsonb/static/src/scss/website_attribute_set.scss",
            "website_attribute_set_jsonb/static/src/js/jsonb_filters.js",
        ],
    },
    "installable": True,
    "auto_install": False,
}
