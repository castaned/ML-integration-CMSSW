import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.utils
from sklearn.model_selection import train_test_split
from utilities.prepare_data import train_data_to_pytorch

def compute_accuracy(outputs, y):
    _, predicted = torch.max(outputs, dim=1)
    correct = (predicted == y).sum().item()
    total = y.size(0)
    acc = correct/total
    return acc

def train_model(model, X, y, ideal_acc, output_dir):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    # Early stopping parameters
    patience = 10
    best_val_loss = float('inf')
    epochs_without_improvement = 0

    # Training loop parameters
    num_epochs = 100
    batch_size = 1024
    val_split = 0.2

    # Split data and transform it to pytorch objects
    train_loader, val_loader = train_data_to_pytorch(X, y, val_split, batch_size)

    # Define the best model checkpoint filename
    checkpoint_path = f'{output_dir}/pytorch_model_best.pth'
    
    # Training loop
    for epoch in range(num_epochs):
        model.train()
        
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            
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
                outputs = model(X_batch)
                val_loss += criterion(outputs, y_batch).item()
                val_acc += compute_accuracy(outputs, y_batch)
                
        val_loss /= len(val_loader)
        val_acc /= len(val_loader)

        print(f"Epoch {epoch + 1}/{num_epochs}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss:.4f}, Val acc: {val_acc:.4f}", flush=True)

        # Early stopping check
        if val_acc >= ideal_acc/100:
            torch.save(model.state_dict(), checkpoint_path)
            print(f"Early stopping: Ideal accuracy reached", flush=True)
            break
        elif val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), checkpoint_path) 
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            
        if epochs_without_improvement >= patience:
            print(f"Early stopping: Validation loss did not improve for {patience} epochs", flush=True)
            break

    return 0
