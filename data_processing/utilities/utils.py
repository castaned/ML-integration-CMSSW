import subprocess
import yaml
import json

def require_key(config, key):
   if key not in config:
      raise KeyError(f"Missing required key in yaml config: '{key}'")
   return config[key]

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

        
def path_to_dir_name(path):
   return path.strip("/").replace("/", "_")

def write_args_file(dat_name, arguments):
   with open(dat_name , "w") as dat_file:
      dat_file.write("\n".join(arguments))

def write_map_file(json_name, data, indent=2):
   with open(json_name , "w") as json_file:
      json.dump(data, json_file, indent=indent)
      
def submit_condor(condor_file):
   exe_cmd(['condor_submit', condor_file])
