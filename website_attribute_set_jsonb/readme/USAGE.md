## Configuration

1. Navigate to **Settings > Technical > Attributes > Attributes**
2. Select a serialized attribute you want to show in website filters
3. Enable **Show in Website Filters**
4. Choose the **Filter Display Type**:
   - **Checkbox**: Multiple selection with checkboxes
   - **Dropdown**: Single selection dropdown
   - **Range Slider**: For numeric/date attributes with min/max input
5. Set the **Website Filter Sequence** to control display order

## Filter Types

### Checkbox Filter
Best for attributes with multiple discrete values where users may want to
select multiple options:
- Brand: Caterpillar, Komatsu, Volvo
- Color: Red, Blue, Green

### Dropdown Filter
Best for single-selection attributes or when there are many values:
- Country of Origin
- Condition (New, Used, Refurbished)

### Range Filter
Best for numeric attributes where users want to filter by range:
- Capacity (kg): 1000 - 5000
- Manufacturing Year: 2020 - 2024
- Operating Weight: 10 - 50 tons

**Note**: Range filters work best when the attribute has a B-tree index
configured in `base_sparse_field_jsonb`.

## URL Parameters

Filter selections are passed as URL parameters:
- Equality: `?jsonb_x_brand=caterpillar,komatsu`
- Range: `?jsonb_range_x_capacity=1000-5000`

This allows for:
- Bookmarkable filtered URLs
- SEO-friendly filter pages
- Integration with external marketing tools
