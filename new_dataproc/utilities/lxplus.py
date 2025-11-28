import os
import sys
import utilities.utils as utils

def expand_proxy_path(path):
   path = os.path.expandvars(os.path.expanduser(path))
   path = path.replace('$(id -u)', str(os.getuid()))
   return path

def generate_proxy(proxy_config):
   proxy_path = utils.require_key(proxy_config, 'proxy_path')
   proxy_path = expand_proxy_path(proxy_path)

   cmd = [
        'voms-proxy-init',
        '--voms', utils.require_key(proxy_config, 'voms'),
        '--valid', utils.require_key(proxy_config, 'proxy_time'),
        '--out', proxy_path
        ]

   utils.exe_cmd(cmd, allow_tty_mode=True)
   print(f'\nTo set env varible in current shell execute: export X509_USER_PROXY={proxy_path}')

   
def das_query_endpoints(redirector, datasets): 
   for dataset in datasets:
      FLN = utils.require_key(dataset, 'FLN')
      ID = utils.require_key(dataset, 'ID')
      amount = utils.require_key(dataset, 'amount')

      cmd = ['dasgoclient', '-query', f'file dataset={FLN}']
      if amount == -1:
         files = utils.exe_cmd(cmd).splitlines()
      else:
         files = utils.exe_cmd(cmd).splitlines()[:amount]
      
      endpoints = [f"root://{redirector}/{f}" for f in files]
      dataset['endpoints'] = endpoints
   return datasets


# This function sets env variables that will be transferred to
# worker nodes using `getenv` in the condor file.
# This reduces the number of arguments for the executable file.
def set_env_vars(proxy_path, eos_output_dir, afs_cms_base, processing_script):
   os.environ['X509_USER_PROXY'] = proxy_path
   os.environ['EOS_OUTPUT_DIR'] = eos_output_dir
   os.environ['AFS_CMS_BASE'] = afs_cms_base
   os.environ['PROCESSING_SCRIPT'] = processing_script
   
def set_env_vars_conversion(tree_name, branches, max_jagged_len):
   os.environ['TREE_NAME'] = tree_name
   os.environ['BRANCHES'] = ",".join(branches) if isinstance(branches, list) else str(branches)
   os.environ['MAX_JAGGED_LEN'] = str(max_jagged_len)

def create_condor_file(condor_params):
   name_file = "processing.jdl"
   exe = utils.require_key(condor_params, "executable_file")
   cpus, gpus, mem, disk = (utils.require_key(condor_params, k) for k in ("cpus","gpus","mem", "disk"))
   job_flavour = utils.require_key(condor_params, "job_flavour")
   
   with open(name_file, "w") as f:
      f.write(f"""universe = vanilla
executable = {exe}
arguments = "$(INPUT_FILE) $(FLN) $(DATASET_DIR)"
getenv = X509_USER_PROXY, EOS_OUTPUT_DIR, AFS_CMS_BASE, PROCESSING_SCRIPT
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
   
def create_condor_convert_file(condor_params):
   name_file = "converting.jdl"
   exe = utils.require_key(condor_params, "executable_file")
   cpus, gpus, mem, disk = (utils.require_key(condor_params, k) for k in ("cpus","gpus","mem", "disk"))
   job_flavour = utils.require_key(condor_params, "job_flavour")
   
   with open(name_file, "w") as f:
      f.write(f"""universe = vanilla
executable = {exe}
arguments = "$(INPUT_FILE) $(OUTPUT_FILE)"
getenv = TREE_NAME, BRANCHES, MAX_JAGGED_LEN
transfer_input_files = conversion_container.sif, ../utilities
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
queue INPUT_FILE OUTPUT_FILE from args_conversion.dat
""")
      return name_file



