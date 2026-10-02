# Configuration

## Pre-built Rule Templates

The module includes these ready-to-use templates:

| Rule | Type | Description |
|------|------|-------------|
| Year (1900-2100) | Range | General year validation |
| Construction Year | Range | Equipment construction years |
| Serial (Alphanumeric) | Regex | 6-20 character serials |
| VIN Number | Regex | 17-character vehicle IDs |
| Country Code | Dynamic | ISO codes from res.country |
| Currency Code | Dynamic | Active currencies |
| Email Address | Regex | Standard email format |
| Phone (International) | Regex | International phone numbers |
| Running Hours | Range | Equipment hour meters |

## Cache Configuration

For dynamic source rules, configure the cache timeout based on how often
the source data changes:

- Static data (countries): 86400 seconds (24 hours)
- Semi-static (brands): 3600 seconds (1 hour)
- Frequently changing: 0 (no cache)

## Security Groups

- **Validation User**: Can use validated fields
- **Validation Manager**: Can create/edit validation rules

Assign users to appropriate groups in Settings > Users.
