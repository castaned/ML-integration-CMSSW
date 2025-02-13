import argparse
import sys
from utilities.prepare_data import get_features_labels
from utilities.read_config_variables import read_variables
from src.optimize_model import train_model
from src.optimize_model import tune_mlp
from src.test_results import test_results 
import datetime
import traceback
import os

# Function to add timestamps to logs
class TimestampedLogger:
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.stream.write(formatted_message)
        with open(self.log_file, "a") as f:
            f.write(formatted_message)

    def flush(self):
        self.stream.flush() 
    
    def fileno(self):
        # Return the file descriptor of the underlying stream
        return self.stream.fileno() if hasattr(self.stream, 'fileno') else None

def main(file_vars):

    output_dir = read_variables(file_vars, ['output_path'])['output_path'][0]
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)
    sys.stdout = TimestampedLogger(sys.stdout, f"{output_dir}/stdout.log")
    sys.stderr = TimestampedLogger(sys.stderr, f"{output_dir}/stderr.log")

    try:
        # Get data
        print("Preparing data...")
        X_train, y_train = get_features_labels(file_vars, remove_mass_pt_window=False)
        num_X_train = X_train.shape[1]
        num_y_train = y_train.shape[1]
        X_test, y_test = get_features_labels(file_vars, test=True)
        print("Data prepared.")

        # Train and optimize model
        print("Training and optimizing model...")
        ideal_acc = read_variables(file_vars, ['ideal_accuracy'])['ideal_accuracy']
        num_models = read_variables(file_vars, ['num_models'])['num_models']
        tune_mlp(X_train, y_train, ideal_acc, num_models, output_dir)
        print("Training and optimization completed.")

        # test model
        print("testing model...")
        test_results(X_test, y_test, 'binary', output_dir)
        print("Testing completed")
        
        
    except Exception as e:
        #print("Error:", e, file=sys.stderr)
        error_message = traceback.format_exc()
        sys.stderr.write(f"[ERROR] {error_message}")

    finally:
        # Reset stdout and stderr, then close the log files
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train IA models")
    parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
    args = parser.parse_args()

    main(args.file)
