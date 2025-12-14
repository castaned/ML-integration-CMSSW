import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.utils
from sklearn.model_selection import train_test_split
import utilities.prepare as prepare
import utilities.learn as learn
import models.models as models
import ray
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from ray.air.integrations.mlflow import MLflowLoggerCallback
from torch.utils.data import DataLoader


def train_model(hyperparam_space, dataset, ideal_acc, output_dir, model_name):
    device = learn.get_device()
    print(f"Device: {device}")

    model = models.MLPmodel(
                  input_size=dataset.num_features, 
                  output_size=dataset.num_classes, 
                  hidden_input_size=hyperparam_space["hidden_input_size"], 
                  hidden_output_size=hyperparam_space["hidden_output_size"], 
                  num_layers=hyperparam_space["num_layers"]
                  ).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=hyperparam_space["learning_rate"])
    print(model)


    patience = hyperparam_space["patience"]
    best_val_loss = float('inf')
    epochs_without_improvement = hyperparam_space["epochs_without_improvement"]

    num_epochs = hyperparam_space["num_epochs"]
    batch_size = hyperparam_space["batch_size"]
    val_split = 0.2

    checkpoint_path = f'{output_dir}/best_model_{model_name}.pth'    

    
    train_dataloader, val_dataloader = prepare.split_and_transform_pythorch(dataset, val_split, batch_size)

    for epoch in range(num_epochs):
        model.train()
        
        for X_batch, y_batch in train_dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            acc = learn.compute_accuracy(outputs, y_batch)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # Gradient clipping
            optimizer.step()
            

        val_loss = 0.0
        val_acc = 0.0
        model.eval()
        with torch.no_grad():
            for X_batch, y_batch in val_dataloader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch)
                val_loss += criterion(outputs, y_batch).item()
                val_acc += learn.compute_accuracy(outputs, y_batch)
                
        val_loss /= len(val_dataloader)
        val_acc /= len(val_dataloader)

        print(f"Epoch {epoch + 1}/{num_epochs}, Train acc: {acc:.4f}, Train loss: {loss.item():.4f}, Val acc: {val_acc:.4f}, Val loss: {val_loss:.4f}")
        tune.report({"loss": val_loss, "acc": val_acc, "val_loss": val_loss, "val_acc": val_acc})

        # Early stopping check
        if val_acc >= ideal_acc/100:
            torch.save({"model_state": model.state_dict(), "hyperparam": hyperparam_space}, checkpoint_path)
            print(f"Early stopping: Ideal accuracy reached")
            break
        elif val_loss < best_val_loss:
            torch.save({"model_state": model.state_dict(), "hyperparam": hyperparam_space}, checkpoint_path)
            best_val_loss = val_loss 
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            
        if epochs_without_improvement >= patience:
            print(f"Early stopping: Validation loss did not improve for {patience} epochs")
            break

    return 0


def tune_mlp(model_name, model_type, dataset, ideal_acc, num_models, output_dir):

    hyperparam_space = {
        "hidden_input_size": tune.choice([64, 128, 256]),
        "hidden_output_size": tune.choice([16, 32, 64]),
        "num_layers": tune.choice([1, 2, 3]),
        "learning_rate": tune.loguniform(1e-4, 1e-2),
        "batch_size": tune.choice([256, 512, 1024]),
        "num_epochs": tune.choice([20]),
        "patience": tune.choice([10]),
        "epochs_without_improvement": tune.choice([10])
    }

    # Hyperparameter tuning scheduler
    scheduler = ASHAScheduler(
        metric="val_loss",
        mode="min",
        max_t=100,
        grace_period=10,
        reduction_factor=2
        )
    
    
    ray.init()
    resources = ray.available_resources()
    num_cpus = int(resources.get("CPU", 1))
    num_gpus = int(resources.get("GPU", 0))
    print(f"CPUs avail: {num_cpus}, GPUs avail: {num_gpus}")
    trainable = tune.with_resources(
         tune.with_parameters(train_model, dataset=dataset, ideal_acc=ideal_acc, output_dir=output_dir, model_name=model_name),
         resources={"cpu": num_cpus, "gpu": num_gpus} 
         )
    #trainable = tune.with_parameters(train_model, dataset=dataset, ideal_acc=ideal_acc, output_dir=output_dir, model_name=model_name)

    mlflow_callback = MLflowLoggerCallback(
                            tracking_uri=f"{output_dir}/mlruns",
                            experiment_name=f"{model_name}",
                            tags={"project": "ML_CMSSW_integration", "model": model_type},
                            save_artifact=True
                            )
    tuner = tune.Tuner(
                 trainable,
                 param_space=hyperparam_space,  
                 tune_config=tune.TuneConfig(
                                  num_samples=num_models,
                                  scheduler=scheduler,
                                  ),
                 run_config=tune.RunConfig(
                                 storage_path=f"{output_dir}/tune_results",
                                 callbacks=[mlflow_callback],
                                 )
                 )
    
    results = tuner.fit()

    best_hyperparam = results.get_best_result(metric="acc", mode="max").config
    best_model = models.MLPmodel(
                       input_size=dataset.num_features, 
                       output_size=dataset.num_classes,
                       hidden_input_size=best_hyperparam["hidden_input_size"], 
                       hidden_output_size=best_hyperparam["hidden_output_size"], 
                       num_layers=best_hyperparam["num_layers"]
                       )

    print("Best hyperparameters found were: ", best_hyperparam)
    print("Best model architecture:", best_model)
    
    learn.convert_to_onnx(dataset.num_features, best_model, output_dir, model_name=f'{model_name}')

    ray.shutdown()
    dataset.close()
    
    return 0
