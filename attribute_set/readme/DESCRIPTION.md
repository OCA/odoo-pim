This module allows the user to create Attributes to any model. This is a
basic module in the way that **it does not provide views to display
these new Attributes.**

Each Attribute created will be related to an **existing field** (in case
of a *"native"* Attribute) or to a newly **created field** (in case of a
*"custom"* Attribute).

A *"custom"* Attribute can be of any type : Char, Text, Boolean, Date,
Binary... but also Many2one or Many2many.

In case of m2o or m2m, these attributes can be related to **custom
options** created for the Attribute, or to **existing Odoo objects**
from other models.

Last but not least an Attribute can be **serialized** using the Odoo SA
module
[base_sparse_field](https://github.com/odoo/odoo/tree/16.0/addons/base_sparse_field)
. It means that all the serialized attributes will be stored in a single
"JSON serialization field" and will not create new columns in the
database (and better, it will not create new SQL tables in case of
Many2many Attributes), **increasing significantly the requests speed**
when dealing with thousands of Attributes.

By default, serialized attributes are stored in a PostgreSQL TEXT column
containing JSON data. While functional, this has performance limitations
for filtering and searching attributes.

For improved performance, especially on e-commerce websites with attribute
filtering, install the ``base_sparse_field_jsonb`` module.

This module upgrades serialized attribute storage to use PostgreSQL's native
JSONB column type with GIN indexing, providing:

* **Fast filtering**: GIN indexes enable efficient key/value lookups
* **Native JSON operators**: Database-level filtering instead of Python
* **Better storage**: Binary format with automatic compression

## Installation

Simply install `base_sparse_field_jsonb` alongside `attribute_set`:

```python
"depends": [
    "attribute_set",
    "base_sparse_field_jsonb",  # Add for JSONB performance
]
```

No configuration required. Existing TEXT columns are automatically migrated
to JSONB on module installation.

### When to use non-serialized attributes

Even with JSONB optimization, consider using non-serialized attributes
(`serialized=False`) for fields that require:

* Heavy range queries (e.g., price ranges, year ranges)
* Sorting in database queries
* Direct SQL JOINs with other tables

For most filtering use cases, serialized JSONB with GIN indexing provides
excellent performance.
