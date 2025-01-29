# New tool for training AI model

This project aims to create a Python-based tool that is as understandable as possible for individuals working in particle physics, particularly in the CMS experiment, who are not familiar with AI models and their optimization but wish to incorporate them into their workflow. In this initial iteration, it is possible to run an MLP (Multilayer Perceptron) model. To run it, modify the `set_config_variables.txt` file. Currently, the variables that can be modified are `train_path`, `test_path`, `output_path`, and `ideal_accuracy`. Follow the specified format in the `set_config_variables.txt` file to set the variables.

## Repository Contents:
* Main file (`main.py`)
* Model training (`src/optimize_model.py`)
* Evaluation and metrics (`src/test_results.py`)
* AI models (`models/models.py`)
* Configuration file reader (`read_config_variables.py`)
* Data formatting script (`prepare_data.py`)
* Required Python libraries (`requirements.txt`)
* Example output directory (`output`)

## How to Use
You need to set all the necessary configurations in the `set_config_variables.txt` file.

### 1. Create an Environment
Ensure you have all the necessary dependencies within the `requirements.txt` file. If you use the virtual environment *venv*, you can install them as follows:

```bash
python -m venv env_path
source env_path/bin/activate 
python install -r requirements.txt
```

### 2. Execute the project
The standard error and output will be generated in the path specified in the `output_path` variable within `set_config_variables.txt`. Run the main scrpit:

```bash
python main.py -f set_config_variables.txt
```

### 3. Outputs
The outputs will also be in the `output_path` directory.

## Next implementations:
1. Templates to run it on ACARUS and LXPLUS.
2. Add optimization functionality for the MLP model.
3. Add another AI model, including its optimization.
4. Improve the logs.