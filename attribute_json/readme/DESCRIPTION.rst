This module allows the user to create attributes to any model. These attributes are stored in a jsonb column in the database.

When a new field of nature json_postgresql is created, we create a field with an inverse, compute, search method that is going to be used to access the jsonb field.
The module also add a new variation of the select type, named selection using the selection field of odoo.

Limitations:

Currently, the module does not support the creation of Many2One, One2Many, Many2Many fields in Odoo. This is because the jsonb type in postgresql does not support the creation of foreign keys.
