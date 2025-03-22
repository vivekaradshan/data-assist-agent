import csv
import json

# Path to the CSV file
csv_file = "table_metadata.csv"

# Dictionary to store schema definitions
schema_definitions = {}

# Read CSV and populate schema dictionary
with open(csv_file, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        table_name = row["Table Name"]
        column_name = row["Column Name"]
        data_type = row["Data Type"]
        key = row["Key"]
        description = row["Description"]

        # Initialize table if not present
        if table_name not in schema_definitions:
            schema_definitions[table_name] = {"columns": []}

        # Add column details
        schema_definitions[table_name]["columns"].append({
            "name": column_name,
            "type": data_type,
            "key": key if key else None,
            "description": description
        })

# Convert dictionary to JSON string (for storage or API usage)
schema_json = json.dumps(schema_definitions, indent=4)

# Print schema definition
print(schema_json)

# Save to a JSON file
with open("schema.json", "w") as json_file:
    json_file.write(schema_json)
