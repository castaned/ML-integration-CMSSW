import argparse
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import utilities.utils as utils
import utilities.root as root


def main(config_path):

    config = utils.load_config(config_path)
    convertion = utils.require_key(config, 'convertion')
    
    input_dirs = utils.require_key(convertion, 'input_dirs')
    tree_name = utils.require_key(convertion,'tree_name')
    branches = utils.require_key(convertion,'branches')
    output_dir = utils.require_key(convertion,'output_dir')
    try:
        max_jagged_len = utils.require_key(convertion, 'max_jagged_len')
    except KeyError:
        max_jagged_len = 10
    
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
            root.root_to_h5(input_path, tree_name, branches, output_path, max_len=max_jagged_len)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NanoAOD root file to h5 file")
    parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
    args = parser.parse_args()
    
    main(args.file)
