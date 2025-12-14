import argparse
import os
import utilities.utils as utils
import utilities.lxplus as lxplus

def main(config_path):

    config = utils.load_config(config_path)
    proxy_config = utils.require_key(config, 'proxy')
    gen_proxy = utils.require_key(proxy_config, 'generate')
    processing_config = utils.require_key(config, 'data_processing')
    redirector = utils.require_key(processing_config, 'redirector')
    datasets = utils.require_key(processing_config, 'datasets')
    eos_output_dir = utils.require_key(processing_config, 'eos_output_dir')
    afs_cms_base = utils.require_key(processing_config, 'afs_cms_base')
    condor_params = utils.require_key(processing_config, 'condor_params')
    processing_script = utils.require_key(processing_config, 'processing_script')
    
    if gen_proxy == 1:
       lxplus.generate_proxy(proxy_config)

    proxy_path = utils.require_key(proxy_config, 'proxy_path')
    proxy_path = lxplus.expand_proxy_path(proxy_path)

    lxplus.set_env_vars_processing(proxy_path, eos_output_dir, afs_cms_base, processing_script)
    
    datasets = lxplus.das_query_endpoints(redirector, datasets)
        
    args_dat = []
    mapping = {}
    for dataset in datasets:
       FLN = dataset["FLN"]
       ID = dataset["ID"]
       endpoints = dataset["endpoints"]
       dataset_dir = f"{eos_output_dir}/{utils.path_to_dir_name(FLN)}"
       
       os.makedirs(dataset_dir, exist_ok=True)

       for i, endpoint in enumerate(endpoints, 1):
          args_dat.append(f"{endpoint}, {FLN}, {dataset_dir}")

       mapping[ID] = FLN

    utils.write_args_file("args_processing.dat", args_dat)

    utils.write_map_file("mapping.json", mapping)

    utils.exe_cmd(['bash', 'set_env.sh'], allow_tty_mode=True)

    name_file = lxplus.create_condor_processing_file(condor_params)
    
    utils.submit_condor(name_file)
       

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Processing NanoAOD root files")
   parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
   args = parser.parse_args()
   
   main(args.file)
