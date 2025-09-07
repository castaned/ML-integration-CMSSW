# Training model

To run it, modify the `set_config_variables.txt` file. Currently, the variables that can be modified are `train_path`, `test_path`, `output_path`, and `ideal_accuracy`. Follow the specified format in the `set_config_variables.txt` file to set the variables.

## Repository Contents:
* Main file (`main.py`)
* Model training (`src/optimize_model.py`)
* Evaluation and metrics (`src/test_results.py`)
* AI models (`models/models.py`)
* Configuration file reader (`read_config_variables.py`)
* Data formatting script (`prepare_data.py`)
* Required Python libraries (`requirements.txt`)
* Example output directory (`output/`)
* SLURM template (`acarus_template.slrm`)
* HTCondor template (`lxplus_template.sub`)
* Executable file for HTCondor (`apptainer_run_training.sh`)
* Apptainer container definition (`tool_container.def`)

## Output directory content:
* MLflow experiments (`mlruns/`)
* Ray Tune optimization results (`tune_results/`)
* Weights and baises from the best models (`best_model_*.pth`)
* Standard output and error logs (`stdout.log` and `stderr.log`)
* Other results
The outputs will be in the `output_path` directory.
