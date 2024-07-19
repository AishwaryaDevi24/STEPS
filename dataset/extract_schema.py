import json

def load_tables_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def extract_table_schemas(data):
    schemas = []
    for item in data:
        db_id = item['db_id']
        table_names = item['table_names_original']
        column_names = item['column_names_original']
        column_types = item['column_types']

        for table_id, table_name in enumerate(table_names):
            schema = {
                'db_id': db_id,
                'table_name': table_name,
                'columns': []
            }

            for column in column_names:
                if column[0] == table_id:
                    column_name = column[1]
                    column_type = column_types[column_names.index(column)]
                    schema['columns'].append((column_name, column_type))
            
            schemas.append(schema)
    return schemas

def save_schemas_to_file(schemas, output_file):
    with open(output_file, 'w') as f:
        for schema in schemas:
            f.write(f"Database ID: {schema['db_id']}\n")
            f.write(f"Table Name: {schema['table_name']}\n")
            f.write("Columns:\n")
            for column in schema['columns']:
                f.write(f"  - {column[0]} ({column[1]})\n")
            f.write("\n")

# Paths to the Spider tables file
tables_file_path = 'dataset/tables.json'

# Load the data
tables_data = load_tables_data(tables_file_path)

# Extract table schemas
table_schemas = extract_table_schemas(tables_data)

# Save schemas to file
save_schemas_to_file(table_schemas, 'dataset/table_schemas.txt')

print("Table schemas extracted and saved.")
