import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.utils
from sklearn.model_selection import train_test_split
from utilities.prepare_data import train_data_to_pytorch
from models.models import MLPmodel
import ray
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from ray.air.integrations.mlflow import MLflowLoggerCallback
import mlflow
import onnx

def compute_accuracy(outputs, y):
    _, predicted = torch.max(outputs, dim=1)
    correct = (predicted == y).sum().item()
    total = y.size(0)
    acc = correct/total
    return acc

def convert_to_onnx(X, model, output_dir):
    
    dummy_input = torch.randn(1, X.shape[1], dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy_input,
        f"{output_dir}/pytorch_best_model.onnx",
        export_params=True,
        opset_version=12,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
    'input': {0: 'batch_size'}, 
    'output': {0: 'batch_size'}
        }
    )

    # Verify
    onnx.checker.check_model(onnx.load(f"{output_dir}/pytorch_best_model.onnx"))
    return 0

def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_model(hyperparam_space, X, y, ideal_acc, output_dir):
    device = get_device()
    print(f"Device: {device}")

    # Init model
    model = MLPmodel(input_size=X.shape[1], 
                     output_size=y.shape[1], 
                     hidden_input_size=hyperparam_space["hidden_input_size"], 
                     hidden_output_size=hyperparam_space["hidden_output_size"], 
                     num_layers=hyperparam_space["num_layers"]
                     ).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=hyperparam_space["learning_rate"])
    print(model)

    # Early stopping parameters
    patience = hyperparam_space["patience"]
    best_val_loss = float('inf')
    epochs_without_improvement = hyperparam_space["epochs_without_improvement"]

    # Training loop parameters
    num_epochs = hyperparam_space["num_epochs"]
    batch_size = hyperparam_space["batch_size"]
    val_split = 0.2

    # Split data and transform it to pytorch objects
    train_loader, val_loader = train_data_to_pytorch(X, y, val_split, batch_size)
    
    # Define the best model checkpoint filename
    checkpoint_path = f'{output_dir}/pytorch_best_model.pth'    
    
    # Training loop
    for epoch in range(num_epochs):
        model.train()
        
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            acc = compute_accuracy(outputs, y_batch)

            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # Gradient clipping
            optimizer.step()
            
        # Validate the model
        val_loss = 0.0
        val_acc = 0.0
        model.eval()
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch)
                val_loss += criterion(outputs, y_batch).item()
                val_acc += compute_accuracy(outputs, y_batch)
                
        val_loss /= len(val_loader)
        val_acc /= len(val_loader)

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


def tune_mlp(X, y, ideal_acc, num_models, output_dir):
    # Search space for hyperparameters
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
        reduction_factor=2)
    
    # Tuning process
    
    ray.init()    
    trainable = tune.with_resources(
        tune.with_parameters(train_model, X=X, y=y, ideal_acc=ideal_acc, output_dir=output_dir),
        resources={"cpu": 20, "gpu": 0} 
    )
    
    # Define the MLflow callback
    mlflow_callback = MLflowLoggerCallback(tracking_uri=f"{output_dir}/mlruns",
                                           experiment_name="test_mlp",
                                           tags={"project": "ML_CMSSW_integration", "model": "mlp"},
                                           save_artifact=True
                                           )
    tuner = tune.Tuner(
        trainable,
        param_space=hyperparam_space,  
        tune_config=tune.TuneConfig(
            num_samples=num_models,
            scheduler=scheduler,
        ),
        run_config=tune.RunConfig(storage_path=f"{output_dir}/tune_results",
                                  callbacks=[mlflow_callback],
                                  )
    )
    
    results = tuner.fit()

    best_hyperparam = results.get_best_result(metric="acc", mode="max").config
    best_model = MLPmodel(input_size=X.shape[1], 
                          output_size=y.shape[1], 
                          hidden_input_size=best_hyperparam["hidden_input_size"], 
                          hidden_output_size=best_hyperparam["hidden_output_size"], 
                          num_layers=best_hyperparam["num_layers"])

    print("Best hyperparameters found were: ", best_hyperparam)
    print("Best model architecture:", best_model)
    
    convert_to_onnx(X, best_model, output_dir)
    return 0
