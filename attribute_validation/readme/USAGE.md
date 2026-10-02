# Usage

## Creating Validation Rules

1. Go to **Settings > Technical > Attribute Validation > Validation Rules**
2. Create a new rule with appropriate type:
   - **Regex**: For pattern matching (e.g., serial numbers, VINs)
   - **Allowed Values**: For static lists
   - **Dynamic Source**: For values from another model
   - **Range**: For numeric boundaries
   - **Python**: For complex custom logic

## Assigning Rules to Attributes

1. Go to the attribute form (Settings > Technical > Attributes)
2. Navigate to the "Validation" tab
3. Add one or more validation rules
4. Enable autocomplete if desired

## Example: Year Validation

For a construction year field that should only accept years 1950-2030:

1. Use the pre-built rule "Construction Year (1950-2030)"
2. Or create a custom range rule:
   - Type: Range
   - Min: 1950
   - Max: 2030
   - Step: 1 (whole numbers only)

## Example: Brand from Dynamic Source

To validate brand names from `product.brand`:

1. Create a Dynamic Source rule:
   - Source Model: Product Brand
   - Source Field: name
   - Cache Timeout: 3600 (1 hour)

2. Assign to your brand attribute
3. Enable autocomplete for dropdown-like behavior
