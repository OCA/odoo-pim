This module provides JSONB optimization for the `attribute_set` module by
integrating with `base_sparse_field_jsonb` from OCA/server-tools.

## Features

### Automatic JSONB Migration
On installation, the module automatically migrates `attribute_set`'s
`x_custom_json_attrs` columns from TEXT to PostgreSQL JSONB format,
providing:

* **Faster filtering**: GIN indexes enable efficient key/value lookups
* **Native JSON operators**: Database-level filtering instead of Python
* **Better storage**: Binary format with automatic compression

### Expression-Based Indexing
For frequently filtered attributes, you can enable per-attribute expression
indexes that provide even faster filtering performance:

1. Go to PIM → Attributes → Product Attributes
2. Edit an attribute and check "Create Expression Index"
3. The module creates an optimized partial index for that specific attribute

This is recommended for attributes used heavily in e-commerce filtering
(e.g., brand, color, material).

### When to Use

Install this module if you:

* Have many serialized attributes (100+)
* Use attribute filtering on e-commerce pages
* Need faster attribute-based searches

### Technical Details

The module creates two types of indexes:

1. **GIN index on JSONB column**: Enables fast key existence checks and
   value lookups across all attributes in the column
2. **Expression indexes (optional)**: Per-attribute indexes for specific
   value extraction, optimal for equality queries on high-traffic attributes
