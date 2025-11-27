import argparse
import uproot
import awkward as ak
import numpy as np
import tables
import sys
import os
import yaml 


def require_key(config, key):
   if key not in config:
      raise KeyError(f"Missing required key in yaml config: '{key}'")
   return config[key]
                
def load_config(config_path):
   with open(config_path) as f:
       return yaml.safe_load(f)

def write_carray(array, h5file, name, group_path='/'):
    h5file.create_carray(group_path, name, obj=array, createparents=True)

def root_to_h5(input_file, tree_name, branches, output_file):
    upfile = uproot.open(input_file)
    tree = upfile[tree_name]

    if branches == "all":
       branches = tree.keys()

    ak_arrays = tree.arrays(branches, library='ak')
    df = ak.to_dataframe(ak_arrays).copy()
    
    with tables.open_file(output_file, mode='w') as h5file:
        for column in df.columns:
           array = df[column].to_numpy()
           write_carray(array, h5file, name=column)

def process_dirs(input_dirs, tree_name, branches, output_dir):

   if not os.path.exists(output_dir):
      os.makedirs(output_dir)

   for input_dir in input_dirs:
      exp_name = os.path.basename(os.path.normpath(input_dir))
      exp_dir = os.path.join(output_dir, exp_name)
      os.makedirs(exp_dir, exist_ok=True)
      
      root_files = [f for f in os.listdir(input_dir) if f.endswith('.root')]
      for root_file in root_files:
         input_path = os.path.join(input_dir, root_file)
         output_path = os.path.join(exp_dir, os.path.splitext(root_file)[0] + '.h5')
         root_to_h5(input_path, tree_name, branches, output_path)


def main(config_path):

   config = load_config(config_path)
   convertion = require_key(config, 'convertion')

   input_dirs = require_key(convertion, 'input_dirs')
   tree_name = require_key(convertion,'tree_name')
   branches = require_key(convertion,'branches')
   output_dir = require_key(convertion,'output_dir')

   process_dirs(input_dirs, tree_name, branches, output_dir)

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Convert NanoAOD root file to h5 file")
   parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
   args = parser.parse_args()
   
   main(args.file)
