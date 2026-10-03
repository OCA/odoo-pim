# Attribute Validation

This module provides data validation for `attribute.attribute` fields from
`product_attribute_set` without requiring Many2one relations.

## Key Features

- **Validation Types**: Regex, allowed values, dynamic source, numeric range, Python expressions
- **Dynamic Sources**: Fetch allowed values from any Odoo model without foreign keys
- **Cascading Rules**: Conditional validation based on other attribute values
- **Autocomplete**: Show suggestions from validation rules in the UI
- **Pre-built Templates**: Common patterns for years, serials, emails, etc.

## Benefits

| Feature | Benefit |
|---------|---------|
| Validation without FK | Keep data in JSONB while enforcing data quality |
| Range queries | Integer/float fields with validation enable BETWEEN queries |
| Dynamic sources | Autocomplete from any model without schema changes |
| Cascading rules | Conditional logic without complex domain expressions |
| Caching | Efficient validation for large datasets |

This enables the best of both worlds: the performance and flexibility of JSONB
storage with the data integrity guarantees typically associated with relational
constraints.
