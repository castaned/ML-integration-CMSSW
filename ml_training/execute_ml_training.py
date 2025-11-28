import argparse
import sys
import utilities.prepare as prepare
import utilities.utils as utils
import utilities.learn as learn
import src.optimize_model as opt
import src.test_results as tr 
import traceback
import os

def main(config_path):

    config = prepare.load_config(config_path)

    data_config = utils.require_key(config, 'data')
    output_dir = utils.require_key(data_config, 'output_path')
    
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    sys.stdout = utils.TimestampedLogger(sys.stdout, f"{output_dir}/stdout.log")
    sys.stderr = utils.TimestampedLogger(sys.stderr, f"{output_dir}/stderr.log")
    
    try:

        input_paths = utils.require_key(data_config, 'input_paths')
        features = utils.require_key(data_config, 'features')
        label = utils.require_key(data_config, 'label')
        num_classes = utils.require_key(data_config, 'num_classes')

        print("Collecting data...")
        full_dataset = prepare.h5Dataset(input_paths, features, label, num_classes)
        train_idx, test_idx = prepare.split_h5Dataset(full_dataset, 0.2, 16)
        train_dataset = prepare.h5Dataset(
                input_paths,
                features,
                label,
                num_classes,
                transform=prepare.MLPTransform(),
                indices=[full_dataset.global_ids[i] for i in train_idx]
            )
        
        test_dataset = prepare.h5Dataset(
                input_paths,
                features,
                label,
                num_classes,
                transform=prepare.MLPTransform(),
                indices=[full_dataset.global_ids[i] for i in test_idx]
            )
        
        print("Data collected.")

        model_config = utils.require_key(config, 'model')
        ideal_acc = utils.require_key(model_config, 'ideal_accuracy')
        num_models = utils.require_key(model_config, 'num_models')
        model_name = utils.require_key(model_config, 'name')
        model_type = utils.require_key(model_config, 'type')
        
        print("Training and optimizing model...")
        if model_type == 'mlp':
            opt.tune_mlp(model_name, model_type, train_dataset, ideal_acc, num_models, output_dir)
            print("MLP training and optimization completed.")
        else:
            print(f"The {model_type} is not available.")
            
        
        print("testing model...")
        if model_type == 'mlp':
            tr.test_results(model_name, model_type, test_dataset, output_dir)
            print("MLP testing completed.")
        else:
            print(f"The {model_type} is not available.")
        
    except Exception as e:
        error_message = traceback.format_exc()
        sys.stderr.write(f"[ERROR] {error_message}")

    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train IA models")
    parser.add_argument('-f', '--file', type=str, help="Path to the configuration file.", required=True)
    args = parser.parse_args()

    main(args.file)
