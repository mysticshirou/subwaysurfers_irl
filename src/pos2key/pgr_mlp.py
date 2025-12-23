import torch
import torch.nn as nn

class PointerMLP(torch.nn.Module):
    def __init__(self, input_size=21, hidden_sizes=[256, 128, 64], num_classes=1):
        super(PointerMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_sizes[0])
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_sizes[0], hidden_sizes[1])
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden_sizes[1], hidden_sizes[2])
        self.relu3 = nn.ReLU()
        self.fc_out = nn.Linear(hidden_sizes[2], num_classes)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.relu3(self.fc3(x))
        x = self.sigmoid(self.fc_out(x))
        return x
