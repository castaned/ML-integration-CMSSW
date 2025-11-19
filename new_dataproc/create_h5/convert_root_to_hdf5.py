import uproot
import awkward as ak
import numpy as np
import tables
import sys
import os
import yaml 

 
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


def main():
   if len(sys.argv) != 2:
      print("Usage: python(3) convert_root_to_h5.py <config.yaml>")
      sys.exti(1)

   config_path = sys.argv[1]
   config = load_config(config_path)['convertion']

   input_dirs = config['input_dirs']
   tree_name = config['tree_name']
   branches = config['branches']
   output_dir = config['output_dir']

   process_dirs(input_dirs, tree_name, branches, output_dir)

if __name__ == "__main__":
   main()
