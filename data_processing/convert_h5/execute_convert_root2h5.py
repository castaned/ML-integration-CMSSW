import argparse
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import utilities.utils as utils
import utilities.lxplus as lxplus
import utilities.root as root

def main(config_path, skip_empty_trees=False, skip_existing=False):
   
   config = utils.load_config(config_path)
   convertion = utils.require_key(config, 'convertion')

   # "condor" (default, HTCondor via `queue ... from args_conversion.dat`) o
   # "slurm" (array job via `#SBATCH --array`).
   scheduler = config.get('scheduler', 'condor')
   if scheduler not in ('condor', 'slurm'):
      raise ValueError(
          f"scheduler invalido: '{scheduler}' (valores permitidos: 'condor', 'slurm')"
      )
   scheduler_params = utils.require_key(
       config, 'condor_params' if scheduler == 'condor' else 'slurm_params'
   )
   conda_env = utils.require_key(convertion, 'conda_env')

   # Raiz del repo (dos niveles arriba de convert_h5/), para el PYTHONPATH
   # de run_conversion.sh.
   project_dir = os.path.dirname(parent_dir)

   input_dirs = utils.require_key(convertion, 'input_dirs')
   tree_name = utils.require_key(convertion,'tree_name')
   branches = utils.require_key(convertion,'branches')
   output_dir = utils.require_key(convertion,'eos_output_dir')
   max_jagged_len = utils.require_key(convertion, 'max_jagged_len')
   skip_empty_trees = skip_empty_trees or convertion.get('skip_empty_trees', False)
   if skip_empty_trees:
      import uproot
   if not max_jagged_len:
      max_jagged_len = 10
      
   if not os.path.exists(output_dir):
      os.makedirs(output_dir)
      
   args_dat = []
   for input_dir in input_dirs:
      exp_name = os.path.basename(os.path.normpath(input_dir))
      exp_dir = os.path.join(output_dir, exp_name)
      os.makedirs(exp_dir, exist_ok=True)
      
      root_files = [f for f in os.listdir(input_dir) if f.endswith('.root')]
      for root_file in root_files:
         input_path = os.path.join(input_dir, root_file)
         output_path = os.path.join(exp_dir, os.path.splitext(root_file)[0] + '.h5')
         if skip_existing and os.path.exists(output_path):
            print(f"Skipping {input_path}: output already exists at {output_path}")
            continue
         if skip_empty_trees:
            with uproot.open(input_path) as source:
               if tree_name not in source:
                  print(f"Skipping {input_path}: no {tree_name} tree (zero selected events)")
                  continue
         args_dat.append(f"{input_path} {output_path}")

   if not args_dat:
      if skip_existing:
         print("No new ROOT files to convert")
         return
      raise ValueError("No ROOT files with a conversion tree were found")
   print(f"Submitting {len(args_dat)} ROOT files for conversion")

   utils.write_args_file("args_conversion.dat", args_dat)

   lxplus.set_env_vars_conversion(tree_name, branches, max_jagged_len, project_dir, conda_env)

   if scheduler == 'condor':
      condor_file = lxplus.create_condor_convert_file(scheduler_params)
      utils.submit_condor(condor_file)
   else:
      slurm_file = lxplus.create_slurm_convert_script(scheduler_params, len(args_dat))
      utils.submit_slurm(slurm_file)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NanoAOD root file to h5 file")
    parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
    parser.add_argument('--skip-empty-trees', action='store_true',
                        help="Skip ROOT files without the configured tree")
    parser.add_argument('--skip-existing', action='store_true',
                        help="Do not reconvert ROOT files whose HDF5 output already exists")
    args = parser.parse_args()
    
    main(args.file, skip_empty_trees=args.skip_empty_trees,
         skip_existing=args.skip_existing)
