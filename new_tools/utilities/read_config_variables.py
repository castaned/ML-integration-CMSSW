# Script to read the variables and convert them to python variables

def convert_types(var_dict):
    for var_name, value in var_dict.items():
        if var_name == 'ideal_accuracy':
            var_dict[var_name] = float(value[0])
        
        if var_name == 'num_models':
            var_dict[var_name] = int(value[0])


def read_variables(file_path, var_names):
    variables = {
        'train_path': [],
        'test_path': [],
        'output_path': [],
        'num_instances': [],
        'features': [],
        'spectators': [],
        'labels': [],
        'ai_model': [],
        'ai_model_class': [],
        'ideal_accuracy': [],
        'num_models': []
    }

    # Check variables are valid
    valid_keys = set(variables.keys())
    invalid_keys = [item for item in var_names if item not in valid_keys]
    if invalid_keys:
        print(f"Error: The following keys are not valid: {invalid_keys}")
        exit(1) 

    # Read the file and extract variable values
    with open(file_path, 'r') as f:
        lines = f.readlines()

    current_var = None
    current_value = []
    inside_list = False
    collecting_values = False

    # Process lines to find the variable assignments
    for line in lines:
        line = line.strip()

        if line.startswith('#') or not line:
            continue

        if '=' in line or inside_list:
            if '[' in line:
                var_name, var_value = line.split('=', 1)
                current_var = var_name.strip()
                inside_list = True
                current_value.append(var_value.strip().strip("[]',"))
            
            if '[' not in line and ']' not in line:
                current_value.append(line.strip().strip("[]',"))

            if ']' in line:
                if '[' not in line:
                    current_value.append(line.strip().strip("[]',"))

                variables[current_var] = current_value
                inside_list = False
                current_value = []
                

    # Filter and convert variables 
    convert_types(variables)
    requested_variables = {key: variables[key] for key in var_names if key in variables}

    return requested_variables
