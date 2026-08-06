## Configuration

1. Navigate to **Settings > Technical > Attributes > Attributes**
2. Select a serialized attribute (integer, float, date, or datetime type)
3. Set **Index Type** to **B-tree (range queries)**

## When to Use

Use B-tree indexes when you need to:
- Filter products by numeric ranges (e.g., capacity: 1000-5000 kg)
- Filter by date ranges (e.g., manufactured after 2020)
- Sort by JSONB attribute values

Use GIN indexes (default) when you need:
- Equality filters (color = 'red')
- Contains/membership queries
- Multiple value selections
