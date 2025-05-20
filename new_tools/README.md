# New tool for training AI model

## It is not finished yet

This project aims to create a Python-based tool that is as understandable as possible for individuals working in particle physics, particularly in the CMS experiment, who are not familiar with AI models and their optimization but wish to incorporate them into their workflow. 

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
If you are running the tool on ACARUS (Área de cómputo de la Universidad de Sonora), submit the SLURM file. If you are at another center that uses SLURM, make the necessary modifications.

```bash
sbatch acarus_template.slrm
```

### 3. Outputs
The outputs will also be in the `output_path` directory. Output directory content:
* MLflow experiments (`mlruns/`)
* Ray Tune optimization results (`tune_results/`)
* Weights and baises from the best models (`best_model_*.pth`)
* Standard output and error logs (`stdout.log` and `stderr.log`)
* Other results

### 4. MLOps
MLflow is used as the MLOps platform. To launch the UI, make sure you are in the environment, then execute:

```bash
mlflow ui --backend-store-uri output_path/mlruns/ --host IP_host --port some_port
```
Then, you can visualize it in your web browser by entering `IP_host:some_port`. Make sure the port is available. Tipically, `localhost` is used as `IP_host`. If you run the code in a computer that you enter through SSH, you need to create a tunnel to redirect the content to your local machine. To do so, execute the following command in your local machine' terminal:

```bash
ssh -N -L local_machine_port:IP_host:remote_machine_port user@remote_IP
```

The `remote_machine_port` and the `some_port` (from the MLflow command) must be the same, as well as the `IP_host`. Additionally, ensure the ports of both machines are available for use. The `-N` prevents execution of other command in the terminal that creates the tunnel, but it is not obligatory. Finally, as mentioned earlier, enter `IP_host:local_machine_port` in your web browser to access the MLflow plataform.

## Next implementations:
1. Template to run it on LXPLUS.
2. Integration into the CMSSW workflow.
3. Add another AI model, including its optimization.
