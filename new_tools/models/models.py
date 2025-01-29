import torch
import torch.nn as nn

# Define  base MLP
class MLPmodel(nn.Module):
    def __init__(self, nfeatures, nlabels):
        super(MLPmodel, self).__init__()
 
        self.bn_1 = nn.BatchNorm1d(nfeatures)
        self.dense_1 = nn.Linear(nfeatures, 64)
        self.dense_2 = nn.Linear(64, 32)
        self.dense_3 = nn.Linear(32, 32)
        self.output = nn.Linear(32, nlabels)

    def forward(self, x):
        x = self.bn_1(x)                                                                    
        x = torch.relu(self.dense_1(x))                                           
        x = torch.relu(self.dense_2(x))
        x = torch.relu(self.dense_3(x))
        x = self.output(x)
        return x
