import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import torch.nn.utils
from sklearn.model_selection import train_test_split

def train_optim(model, X, y, output_dir):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    # Early stopping parameters
    patience = 10
    best_val_loss = float('inf')
    epochs_without_improvement = 0

    # Training loop parameters
    num_epochs = 100
    batch_size = 1024
    validation_split = 0.2

    # Split data and transform it to pytorch objects
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=validation_split, shuffle=True)

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.argmax(torch.tensor(y_train, dtype=torch.long), dim=1)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.argmax(torch.tensor(y_val, dtype=torch.long), dim=1)
    
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
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
        model.eval()
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                outputs = model(X_batch)
                val_loss += criterion(outputs, y_batch).item()
                
        val_loss /= len(val_loader)

        print(f"Epoch {epoch + 1}/{num_epochs}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss:.4f}", flush=True)

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), checkpoint_path) 
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            
        if epochs_without_improvement >= patience:
            print(f"Early stopping: Validation loss did not improve for {patience} epochs", flush=True)
            break

    return 0
