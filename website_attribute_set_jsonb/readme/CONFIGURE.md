## Prerequisites

1. Install `attribute_set` from OCA/odoo-pim
2. Install `base_sparse_field_jsonb` for JSONB support
3. Create serialized attributes on `product.template`

## Index Configuration

For optimal performance, configure indexes based on filter type:

### Equality Filters (checkbox, dropdown)
Set **Index Type** to **GIN (equality/containment)** on the attribute.

### Range Filters
Set **Index Type** to **B-tree (range queries)** on the attribute.

## Template Customization

The filter template can be customized by inheriting:
- `website_attribute_set_jsonb.jsonb_attributes_filter`
- `website_attribute_set_jsonb.products_jsonb_attributes`

Example:
```xml
<template id="custom_jsonb_filter" inherit_id="website_attribute_set_jsonb.jsonb_attributes_filter">
    <xpath expr="//div[hasclass('accordion-body')]" position="attributes">
        <attribute name="class" add="custom-filter-body"/>
    </xpath>
</template>
```

## Styling

Override SCSS variables or add custom styles:
```scss
.o_jsonb_attribute_filter {
    .accordion-body {
        max-height: 400px;  // Increase max height
    }
}
```
