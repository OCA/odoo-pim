This module extends OCA's `attribute_set_jsonb` with B-tree expression index
support for range queries on numeric and date serialized attributes.

## Features

- **Index Type Selection**: Choose between GIN (equality) and B-tree (range) indexes
- **B-tree Expression Indexes**: Creates PostgreSQL B-tree indexes with proper type casting
- **Range Query Support**: Enables efficient >, <, >=, <=, BETWEEN queries on JSONB values
- **Automatic Type Casting**: Casts JSONB values to integer, numeric, date, or timestamp

## Supported Attribute Types

B-tree indexes can be created for:
- `integer` - Cast to PostgreSQL integer
- `float` - Cast to PostgreSQL numeric
- `date` - Cast to PostgreSQL date
- `datetime` - Cast to PostgreSQL timestamp

## Performance

B-tree indexes enable PostgreSQL to use index scans for range queries:
```sql
-- Without B-tree index: Sequential scan
-- With B-tree index: Index scan
SELECT * FROM product_template
WHERE (x_custom_json_attrs->>'x_capacity')::numeric BETWEEN 1000 AND 5000
```
