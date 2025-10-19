# koatoth Utilities

This folder contains utilities for working with the koatoth (Класифікатор об'єктів адміністративно-територіального устрою України) dataset - the Ukrainian administrative-territorial structure classifier.

## Overview

koatoth is the official classification of administrative-territorial units of Ukraine, containing hierarchical data about regions, districts, territorial communities, cities, villages, and settlements.

## Files

- `convert_koatoth_csv.py` - Python script to convert koatoth CSV from ID-based format to human-readable format
- `README.md` - This documentation file

## Data Structure

The koatoth dataset contains Ukrainian administrative divisions in a hierarchical structure:

- **Level 1 (O)**: Regions/Oblasts (Області) - e.g., "Автономна Республіка Крим", "Вінницька"
- **Level 2 (P)**: Districts/Rayons (Райони) - e.g., "Бахчисарайський", "Вінницький"  
- **Level 3 (H)**: Territorial communities/Hromadas (Територіальні громади) - e.g., "Андріївська", "Агрономічна"
- **Level 4 (C, M, X)**: Cities, villages, settlements (Міста, села, селища) - e.g., "Андріївка", "Бахчисарай"

## Conversion Script

### Purpose

The `convert_koatoth_csv.py` script converts the original koatoth CSV file from a format using cryptic UAXXXXX IDs to a more readable format with human-readable names and types.

### Input Format

Original koatoth CSV with columns:
- Columns 0-4: Hierarchical IDs (UAXXXXX format)
- Column 5: Category code (O, P, H, C, M, X)
- Column 6: Name of the administrative unit

### Output Format

Converted CSV with 4 columns:
- **id**: The record ID (UAXXXXX format) - kept intact
- **parents**: Comma-separated list of parent names with their types (e.g., "Автономна Республіка Крим область, Бахчисарайський район")
- **type**: Ukrainian category name in lowercase (область, район, територіальна громада, місто, село, селище)
- **name**: The name of the administrative unit

### Type Mappings

| Code | Ukrainian Type (Capitalized) | Ukrainian Type (Lowercase) |
|------|------------------------------|----------------------------|
| O    | Область                      | область                    |
| P    | Район                        | район                      |
| H    | Територіальна громада        | територіальна громада      |
| M    | Місто                        | місто                      |
| C    | Село                         | село                       |
| X    | Селище                       | селище                     |

### Usage

```bash
python convert_koatoth_csv.py <input_file> <output_file>
```

**Example:**
```bash
python convert_koatoth_csv.py koatoth.csv koatoth_converted.csv
```

### Example Conversion

**Input:**
```csv
UA01000000000013043;UA01020000000022387;UA01020010000048857;UA01020010010075540;;C;Андріївка
```

**Output:**
```csv
UA01020010010075540;Автономна Республіка Крим область, Бахчисарайський район, Андріївська територіальна громада;село;Андріївка
```

## Performance

The conversion script is optimized for performance using hash maps for O(1) lookups instead of linear searches, making it suitable for processing large datasets efficiently.

## Data Source

The koatoth dataset is the official Ukrainian administrative-territorial structure classification maintained by the State Statistics Service of Ukraine.

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## License

This utility script is provided as-is for processing koatoth data. Please ensure compliance with the original data source licensing terms.
