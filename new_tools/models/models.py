import torch
import torch.nn as nn

# Define  base MLP
class MLPmodel(nn.Module):
    def __init__(self, input_size, output_size, hidden_input_size, hidden_output_size, num_layers):
        super(MLPmodel, self).__init__()
 
        layers = []
        layers.append(nn.Linear(input_size,  hidden_input_size))
        layers.append(nn.ReLU())
        
        hidden_size = hidden_input_size
        for i in range(num_layers - 1):
            layers.append(nn.Linear(hidden_size,  hidden_size))
            layers.append(nn.ReLU())
            if i == num_layers-2:
                layers.append(nn.Linear(hidden_size, hidden_output_size))
                layers.append(nn.ReLU())
                hidden_size = hidden_output_size

        if num_layers == 1:
            layers.append(nn.Linear(hidden_input_size, output_size))
        else:
            layers.append(nn.Linear(hidden_output_size, output_size))
        
        self.net = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.net(x)
