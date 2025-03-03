import os
import yaml
import subprocess

# ========= CONFIGURATION =========
YAML_FILE = "datasets.yaml"  # Input YAML file with datasets
JDL_FILE = "condor_submit.jdl"
X509_PROXY = os.path.expanduser("~/.globus/x509up_u29575")  # Proxy path
JOB_SCRIPT = "run_filter.sh"  # Job execution script
EOS_BASE_DIR = "/eos/user/c/castaned/NanoAOD_Filtered"  # Modify for your EOS path
# =================================


def get_files_from_das(dataset):
    """Query DAS to get list of files and prepend xrootd prefix"""
    cmd = f"dasgoclient --query='file dataset={dataset}'"
    try:
        output = subprocess.check_output(cmd, shell=True).decode().split()
        if not output:
            print(f"No files found for {dataset}")
            return []
        files = [f"root://cms-xrd-global.cern.ch/{f}" for f in output]
        return files
    except subprocess.CalledProcessError as e:
        print(f"DAS Query Failed: {e}")
        return []

def sanitize_dataset_name(dataset):
    """Sanitize dataset name to use as folder name (remove slashes)."""
    return dataset.strip("/").replace("/", "_")

def load_datasets(yaml_file):
    """Load dataset names from YAML file."""
    with open(yaml_file, "r") as f:
        datasets = yaml.safe_load(f)
    return datasets["datasets"]

def create_condor_jdl(input_files, output_dir):
    """Generate Condor JDL file dynamically."""
    with open(JDL_FILE, "w") as f:
        f.write(f"""universe = vanilla
executable = {JOB_SCRIPT}
output = logs/job_$(ClusterId)_$(Process).out
error = logs/job_$(ClusterId)_$(Process).err
log = logs/job_$(ClusterId)_$(Process).log
request_cpus = 1
request_memory = 2000M
request_disk = 2GB
should_transfer_files = YES
transfer_input_files = filterNanoAOD.py
+JobFlavour = "workday"
x509userproxy = {X509_PROXY}
""")
        for file in input_files:
            output_file = f"{output_dir}/filtered_{os.path.basename(file)}"
            f.write(f'arguments = {file} {output_file}\nqueue\n')
    print(f"Condor JDL `{JDL_FILE}` created!")

def submit_condor():
    """Submit Condor jobs."""
    os.system(f"condor_submit {JDL_FILE}")
    print("Jobs submitted to Condor!")

def main():
    """Main function to process datasets and submit jobs."""
    datasets = load_datasets(YAML_FILE)
    for dataset in datasets:
        dataset_folder = sanitize_dataset_name(dataset)
        output_dir = f"{EOS_BASE_DIR}/{dataset_folder}"
        
        # Ensure EOS directory exists
        os.makedirs(output_dir, exist_ok=True)

        files = get_files_from_das(dataset)
        if files:
            create_condor_jdl(files, output_dir)
            submit_condor()

if __name__ == "__main__":
    main()
