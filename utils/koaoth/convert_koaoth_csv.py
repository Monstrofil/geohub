#!/usr/bin/env python3
"""
Script to convert koatoth CSV file from ID-based format to text-based format.
Replaces parent level IDs (UAXXXXX) with their corresponding text names.

The koatoth (Класифікатор об'єктів адміністративно-територіального устрою України)
file contains Ukrainian administrative divisions in a hierarchical structure:

- Level 1 (O): Regions/Oblasts (Області)
- Level 2 (P): Districts/Rayons (Райони)  
- Level 3 (H): Territorial communities/Hromadas (Територіальні громади)
- Level 4 (C, M, X): Cities, villages, settlements (Міста, села, селища)

Input: CSV with hierarchical Ukrainian administrative divisions using UAXXXXX IDs
Output: JSON with objects containing: id, parents, type, name

Example:
Before: UA01000000000013043;UA01020000000022387;UA01020010000048857;UA01020010010075540;;C;Андріївка
After:  {
  "id": "UA01020010010075540",
  "parents": "Автономна Республіка Крим область, Бахчисарайський район, Андріївська територіальна громада",
  "type": "село",
  "name": "Андріївка"
}

Output format:
- id: The record ID (UAXXXXX format)
- parents: Comma-separated list of parent names
- type: Ukrainian category names (Область, Район, Територіальна громада, Місто, Село, Селище)
- name: The name of the administrative unit

Usage: python convert_koatoth_csv.py <input_file> <output_file>
"""

import csv
import json
import sys
from collections import defaultdict


def read_koatoth_csv(input_file):
    """Read the koatoth CSV file and build mappings of IDs to names and types."""
    id_to_name = {}
    id_to_type = {}
    rows = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        
        for row in reader:
            if len(row) < 7:
                continue
                
            rows.append(row)
            
            # Find the deepest level ID in this row (rightmost non-empty ID)
            deepest_id = None
            for i in range(5, -1, -1):  # Check from right to left
                if row[i] and row[i].startswith('UA'):
                    deepest_id = row[i]
                    break
            
            # Map this deepest ID to the name and type
            if deepest_id:
                id_to_name[deepest_id] = row[6]
                category_code = row[5] if len(row) > 5 else ''
                id_to_type[deepest_id] = category_code
    
    return rows, id_to_name, id_to_type


def get_type_description(category_code, lowercase=False):
    """Convert category code to Ukrainian human readable form."""
    type_mapping = {
        'O': 'область' if lowercase else 'Область',
        'P': 'район' if lowercase else 'Район',
        'H': 'територіальна громада' if lowercase else 'Територіальна громада',
        'M': 'місто' if lowercase else 'Місто',
        'C': 'село' if lowercase else 'Село',
        'X': 'селище' if lowercase else 'Селище'
    }
    return type_mapping.get(category_code, category_code)


def convert_row(row, id_to_name, id_to_type):
    """Convert a single row to the new format as a dictionary: id, parents, type, name."""
    # Find the deepest level ID (record ID) - this is our ID
    record_id = None
    parent_names = []
    
    # Find all IDs in the row
    ids_in_row = []
    for i, cell in enumerate(row[:6]):  # Process first 6 columns (ID columns)
        if cell and cell.startswith('UA'):
            ids_in_row.append((i, cell))
    
    if not ids_in_row:
        return {'id': '', 'parents': '', 'type': '', 'name': ''}
    
    # The last ID in the row is the record ID
    record_id = ids_in_row[-1][1]
    
    # All other IDs are parent IDs - we need to find their types too
    for i, parent_id in ids_in_row[:-1]:
        parent_name = id_to_name.get(parent_id, parent_id)
        if parent_name and parent_name != parent_id:  # Only add if we have a text name
            # Clean up the name by removing trailing spaces
            clean_name = parent_name.strip()
            # Get the type for this parent ID from the hash map
            parent_category = id_to_type.get(parent_id, '')
            if parent_category:
                parent_type = get_type_description(parent_category, lowercase=True)
                parent_with_type = f"{clean_name} {parent_type}"
                parent_names.append(parent_with_type)
            else:
                parent_names.append(clean_name)
    
    # Get the category and name from the original row
    # Column 5 (index 5) is "Категорія об'єкта" and column 6 (index 6) is "Назва об'єкта"
    category_code = row[5] if len(row) > 5 else ''
    name = row[6] if len(row) > 6 else ''
    
    # Clean up the name by removing trailing spaces
    clean_name = name.strip()
    
    # Convert category to human readable form (lowercase for final record)
    type_description = get_type_description(category_code, lowercase=True)
    
    # Join parent names with comma and space
    parents_str = ', '.join(parent_names)
    
    return {'id': record_id, 'parents': parents_str, 'type': type_description, 'name': clean_name}


def convert_koatoth_csv(input_file, output_file):
    """Convert the koatoth CSV file to JSON format."""
    print(f"Reading input file: {input_file}")
    rows, id_to_name, id_to_type = read_koatoth_csv(input_file)
    
    print(f"Found {len(id_to_name)} ID mappings")
    print(f"Processing {len(rows)} rows")
    
    # Convert all rows to JSON format
    json_data = []
    
    # Skip the first row (header) and process data rows
    for row in rows[1:]:
        converted_row = convert_row(row, id_to_name, id_to_type)
        json_data.append(converted_row)
    
    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete! Output written to: {output_file}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python convert_koatoth_csv.py <input_file> <output_file>")
        print("Example: python convert_koatoth_csv.py koatoth.csv koatoth_converted.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        convert_koatoth_csv(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
