import argparse, csv, json

# Parse CLI args
cli_arg_parser = argparse.ArgumentParser()
cli_arg_parser.add_argument('json_file_path', help='path to input json file')
cli_arg_parser.add_argument('csv_file_path', help='path to output csv file')
cli_args = cli_arg_parser.parse_args()

json_file_path = cli_args.json_file_path
csv_file_path = cli_args.csv_file_path

print(f'Transform of {json_file_path} to {csv_file_path} starting...')

# Parse JSON file
with open(json_file_path) as json_file:
    json_data_points = json.load(json_file)

# Generate dict for CSV data
csv_data_points = []
po_1_lookup = {}

for data_point in json_data_points['data_points']:
    data_point_title = data_point['title']
    data_point_rules_section = data_point['rule_section']

    for data_field in data_point['data_fields']:

        short_name = data_field['short_name']

        valid_value_codes = ''
        valid_value_descriptions = ''
        valid_values = data_field.get('valid_values',None)

        examples = '; '.join(x for x in data_field['examples'])
        validations = '; '.join(x for x in data_field['validations'])

        if valid_values:
            # Drop the header record
            valid_values.pop(0)

            valid_value_codes = ';'.join([str(x[0]) for x in valid_values])
            valid_value_descriptions = '; '.join([x[1] for x in valid_values])

        # NOTE: Embedded HTML is not a great fit for translating to CSV 
        instructions = data_field['instruction_text']

        rule_section = data_field.get('citation', None) or data_point_rules_section

        # Row in the CSV
        csv_data_point = {
            'field_number': data_field['field_number'],
            'data_point': data_point_title,
            'data_field_title': data_field['title'],
            'column_name': short_name,
            'data_type': data_field['type'],
            'valid_value_codes': valid_value_codes,
            'valid_value_descriptions': valid_value_descriptions,
            'conditionality': data_field['conditionality'],
            'instructions': instructions,
            'rule_section': rule_section,
            'examples': examples,
            'validations': validations,
        }

        # Special handling for po_x_* fields, copying po_1 fields to related po_2, po_3, and po_4 fields.
        if short_name.startswith('po_'):
            po_num = short_name[3]
            if po_num == '1':
                po_1_lookup[short_name] = csv_data_point
            else:
                po_1_short_name = f'po_1_{short_name[5:]}'
                csv_data_point['valid_value_codes'] = po_1_lookup[po_1_short_name]['valid_value_codes']
                csv_data_point['valid_value_descriptions'] = po_1_lookup[po_1_short_name]['valid_value_descriptions']
                csv_data_point['examples'] = po_1_lookup[po_1_short_name]['examples']
                csv_data_point['validations'] = po_1_lookup[po_1_short_name]['validations']

                po_1_instructions = po_1_lookup[po_1_short_name]['instructions']
                csv_data_point['instructions'] = po_1_instructions.replace('owner 1', f'owner {po_num}').replace('owner: 1', f'owner: {po_num}')

        csv_data_points.append(csv_data_point)

# Write CSV data to file
with open(csv_file_path, 'w') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=csv_data_points[0].keys())
    writer.writeheader()
    writer.writerows(csv_data_points)

print(f'Transform of {json_file_path} to {csv_file_path} complete')
