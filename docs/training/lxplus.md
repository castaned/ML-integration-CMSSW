# Run tool in LXPLUS at CERN

## How to Use
You need to set all the necessary configurations in the `set_config_variables.txt` file.

### 1. Create an Environment
Ensure you have all the necessary dependencies within the `requirements.txt` file. When using HTCondor in LXPLUS to send a job, a sandbox  is created cointaining all transferred files. To streamline this, we recommend creating a containerized environment and submitting it. We can do it as follows:

```bash
apptainer build tool_container.sif tool_container.def
```

### 2. Execute the project
The standard error and output will be generated in the path specified in the `output_path` variable within `set_config_variables.txt`. To run the tool, we need to create a HTCondor file, `lxplus_template.sub` can be used as a template, just replace variable values with your information. If you are at another center that uses HTCondor, make the necessary modifications.

```bash
condor_submit lxplus_template.sub
```

The main file is `apptainer_run_training.sh`, which will run the code inside the container within the sandbox. The data to be used was prepared beforehand and stored as a tar file in the EOS system. In this main file, the data is descompressed for use.

### 4. MLOps
MLflow is used as the MLOps platform. To launch the UI, just execute the following command using the apptainer container created in step 1:

```bash
apptainer exec tool_container.sif mlflow ui --backend-store-uri output_path/mlruns/ --host IP_host --port some_port
```

Then, you can visualize it in your web browser by entering `IP_host:some_port`. However, in LXPLUS, it is not possible to visualize it directly, we need to create a tunnel to redirect the content to your local machine. To do so, execute the following command in your local machine's terminal:

```bash
ssh -N -L local_machine_port:IP_host:remote_machine_port user@lxplus.cern.ch -J user@remote_IP_where_mlflow_server_running
```
 
To get the `remote_IP_where_mlflow_server_running`, run the command:

```bash
hostname -I
```

The first IP is the server's IP where the MLflow server is running. The `remote_machine_port` and the `some_port` (from the MLflow command) must be the same, as well as the `IP_host`. Additionally, ensure the ports of both machines are available for use. The `-N` prevents execution of other command in the terminal that creates the tunnel, but it is not obligatory. Finally, enter the `IP_host:local_machine_port` in your web browser to access the MLflow platform.
