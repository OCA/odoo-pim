This module integrates OCA's `attribute_set` JSONB serialized attributes with
Odoo's website shop filtering system.

**Features**

- **Website Visibility Configuration**: Mark JSONB attributes as visible in
  website shop filters
- **Multiple Filter Types**: Support for checkbox, dropdown, and range slider
  filters
- **Facet Counting**: Displays count of products matching each filter value
- **Range Queries**: Efficient range filtering for numeric/date attributes
  using B-tree indexes
- **URL Parameter Preservation**: Filter selections persist across pagination
  and sorting
- **Active Filter Tags**: Visual display of currently applied filters with
  easy removal

**Use Cases**

- Heavy equipment dealers: Filter machines by capacity, year, brand
- E-commerce sites: Filter products by custom dynamic attributes
- B2B portals: Filter by technical specifications stored in JSONB

**Performance**

This module uses PostgreSQL JSONB operators directly for efficient filtering:

- GIN indexes for equality/containment queries
- B-tree expression indexes for range queries (>, <, BETWEEN)
- Direct SQL for facet counting to avoid ORM overhead
