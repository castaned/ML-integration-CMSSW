import argparse
import sys
from utilities.prepare_data import get_features_labels
from utilities.read_config_variables import read_variables
from models.models import MLPmodel 
from src.optimize_model import train_model
from src.test_results import test_results 
 

def main(file_vars):

    output_dir = read_variables(file_vars, ['output_path'])['output_path'][0]
    stdout_file = open(f"{output_dir}/stdout.log", "w")
    stderr_file = open(f"{output_dir}/stderr.log", "w")
    sys.stdout = stdout_file
    sys.stderr = stderr_file

    try:
        # Get data
        print("Preparing data...", flush=True)
        X_train, y_train = get_features_labels(file_vars, remove_mass_pt_window=False)
        num_X_train = X_train.shape[1]
        num_y_train = y_train.shape[1]
        X_test, y_test = get_features_labels(file_vars, test=True)
        #print("X_train shape:", X_train.shape)
        #print("y_train shape:", y_train.shape)
        #print("X_test shape:", X_test.shape)
        #print("y_test shape:", y_test.shape)
        print("Data prepared.\n", flush=True)

        # Get base model
        print("Loading model...", flush=True)
        base_model = MLPmodel(nfeatures=num_X_train, nlabels=num_y_train)
        print("Base model architecture:", flush=True)
        print(base_model, flush=True)
        print ("Model loaded.\n", flush=True)
        
        # Train and optimize model
        print("Training and optimizing model...", flush=True)
        ideal_acc = read_variables(file_vars, ['ideal_accuracy'])['ideal_accuracy']
        train_model(base_model, X_train, y_train, ideal_acc, output_dir)
        print("Training and optimization completed.\n", flush=True)

        # test model
        print("testing model...", flush=True)
        test_results(base_model, X_test, y_test, 'binary', output_dir)
        print("Testing completed\n", flush=True)
        
        
    except Exception as e:
        print("Error:", e, file=sys.stderr, flush=True)
    
    finally:
        # Reset stdout and stderr, then close the log files
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        stdout_file.close()
        stderr_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train IA models")
    parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
    args = parser.parse_args()

    main(args.file)
