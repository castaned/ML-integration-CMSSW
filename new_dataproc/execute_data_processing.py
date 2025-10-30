import os
import subprocess
import sys
import yaml
import json

def load_config(config_path):
   with open(config_path) as f:
       return yaml.safe_load(f)

    
def exe_cmd(cmd, allow_tty_mode=False):
   if isinstance(cmd, str):
      cmd = cmd.split()
      
   try:
      if allow_tty_mode:
         result = subprocess.run(cmd, check=True)
         return None
      else:
         result = subprocess.run(cmd, check=True, capture_output=True, text=True)
         return result.stdout
   except subprocess.CalledProcessError as e:
      print(f"Error: {e.stderr}")
      return None

        
def expand_proxy_path(path):
   path = os.path.expandvars(os.path.expanduser(path))
   path = path.replace('$(id -u)', str(os.getuid()))
   return path

def generate_proxy(proxy_config): 
   proxy_path = expand_proxy_path(proxy_config['proxy_path'])

   cmd = [
        'voms-proxy-init',
        '--voms', proxy_config['voms'],
        '--valid', proxy_config['proxy_time'],
        '--out', proxy_path
        ]

   exe_cmd(cmd, allow_tty_mode=True)
   print(f'\nTo set env varible in current shell execute: export X509_USER_PROXY={proxy_path}')

   
def das_query_endpoints(redirector, datasets): 
   for dataset in datasets:
      FLN = dataset['FLN']
      ID = dataset['ID']
      amount = dataset['amount'] 

      cmd = ['dasgoclient', '-query', f'file dataset={FLN}']
      if amount == -1:
         files = exe_cmd(cmd).splitlines()
      else:
         files = exe_cmd(cmd).splitlines()[:amount]
      
      endpoints = [f"root://{redirector}/{f}" for f in files]
      dataset['endpoints'] = endpoints
   return datasets


def path_to_dir_name(path):
   return path.strip("/").replace("/", "_")

# This function sets env variables that will be transferred to
# worker nodes using `getenv = True` in the condor file.
# This reduces the number of arguments for the executable file.
def set_env_vars(proxy_path, eos_output_dir, afs_cms_base, processing_script):
   os.environ['X509_USER_PROXY'] = proxy_path
   os.environ['EOS_OUTPUT_DIR'] = eos_output_dir
   os.environ['AFS_CMS_BASE'] = afs_cms_base
   os.environ['PROCESSING_SCRIPT'] = processing_script
   
   
def create_condor_file(condor_params):
   name_file = "processing.jdl"
   exe = condor_params["executable_file"]
   cpus, gpus, mem, disk = (condor_params[k] for k in ("cpus","gpus","mem", "disk"))
   job_flavour = condor_params["job_flavour"]
   
   with open(name_file, "w") as f:
      f.write(f"""universe = vanilla
executable = {exe}
arguments = "$(INPUT_FILE) $(FLN) $(DATASET_DIR)"
getenv = True
output = logs/job_$(ClusterId)_$(ProcId).out
error = logs/job_$(ClusterId)_$(ProcId).err
log = logs/job_$(ClusterId)_$(ProcId).log
request_cpus = {cpus}
request_gpus = {gpus}
request_memory = {mem}
request_disk = {disk}
+JobFlavour = {job_flavour}
retry = 5
transfer_output_files = ""
queue INPUT_FILE, FLN, DATASET_DIR from args.dat
""")
      return name_file


def submit_condor(condor_file):
   exe_cmd(['condor_submit', condor_file])

      
def main():
    if len(sys.argv) < 2:
        print("Usage: Python(3) execute_data_processing.py <config.yaml>")


    config_path = sys.argv[1]
    config = load_config(config_path)
    proxy_config = config["proxy"]
    gen_proxy = proxy_config["generate"]
    processing_config = config["data_processing"]
    redirector = processing_config["redirector"]
    datasets = processing_config["datasets"]
    eos_output_dir = processing_config["eos_output_dir"]
    afs_cms_base = processing_config["afs_cms_base"]
    condor_params = processing_config["condor_params"]
    processing_script = processing_config["processing_script"]
    
    if gen_proxy == 1:
       generate_proxy(proxy_config)

    proxy_path = expand_proxy_path(proxy_config['proxy_path'])
    set_env_vars(proxy_path, eos_output_dir, afs_cms_base, processing_script)
    
    datasets = das_query_endpoints(redirector, datasets)
    
    exe_cmd(['bash', 'set_env.sh'], allow_tty_mode=True)
    

    name_file = create_condor_file(condor_params)
    args_dat = []
    mapping = {}
    for dataset in datasets:
       FLN = dataset["FLN"]
       ID = dataset["ID"]
       endpoints = dataset["endpoints"]
       dataset_dir = f"{eos_output_dir}/{path_to_dir_name(FLN)}"
       
       os.makedirs(dataset_dir, exist_ok=True)

       for i, endpoint in enumerate(endpoints, 1):
          args_dat.append(f"{endpoint}, {FLN}, {dataset_dir}")

       mapping[ID] = FLN

    with open("args.dat" , "w") as f:
       f.write("\n".join(args_dat))

    with open("mapping.json" , "w") as f:
       json.dump(mapping, f, indent=2)

         
    submit_condor(name_file)
       

if __name__ == "__main__":
    main()
