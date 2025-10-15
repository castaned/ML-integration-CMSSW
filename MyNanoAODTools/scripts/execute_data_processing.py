import os
import subprocess
import sys
import yaml


def load_config(config_path):
   with open(config_path) as f:
       return yaml.safe_load(f)

    
def exe_cmd(cmd, allow_interactive=False):
   if isinstance(cmd, str):
      cmd = cmd.split()
      
   try:
      if allow_interactive:
         result = subprocess.run(cmd, check=True)
         return None
      else:
         result = subprocess.run(cmd, check=True, capture_output=True, text=True)
         return result.stdout
   except subprocess.CalledProcessError as e:
      print(f"Error: {e.stderr}")
      return None

        
def expand_path(path):
   path = os.path.expandvars(os.path.expanduser(path))
   path = path.replace('$(id -u)', str(os.getuid()))
   return path

def generate_proxy(proxy_config): 
   proxy_path = expand_path(proxy_config['proxy_path'])

   cmd = [
        'voms-proxy-init',
        '--voms', proxy_config['voms'],
        '--valid', proxy_config['proxy_time'],
        '--out', proxy_path
        ]

   exe_cmd(cmd, allow_interactive=True)
   os.environ['X509_USER_PROXY'] = proxy_path
   subprocess.run(['voms-proxy-info', '--all'])
   print(f'\nTo set env varible in current shell execute: export X509_USER_PROXY={proxy_path}')

   
def main():
    if len(sys.argv) < 2:
        print("Usage: Python(3) execute_data_processing.py <config.yaml>")


    config_path = sys.argv[1]
    config = load_config(config_path)
    proxy_config = config["proxy"]
    gen_proxy = proxy_config["generate"]

    if gen_proxy == 1:
       generate_proxy(proxy_config)
    
if __name__ == "__main__":

    main()
