import torch.nn as nn
import torchvision

class MLP(nn.Module):
        def __init__(self):
            super(MLP, self).__init__()
            self.layers = nn.Sequential(
                nn.Linear(21, 100),
                nn.ReLU(),
                nn.Linear(100, 100),
                nn.ReLU(),
                nn.Linear(100, 1)
            )
            
        def forward(self, x):
            x = self.layers(x)
            return x
        
class resNet(nn.Module):
    """
    Use restnet from torchvision
    """

    def __init__(self, layers="18", pre_trained=False):
        super(resNet, self).__init__()
        if layers == "18":
            self.model = torchvision.models.resnet18(pretrained=pre_trained)
        else:
            raise NotImplementedError

    def forward(self, x):
        return self.model(x)
        


class CNN(nn.Module):
    def __init__(self, resnet=False, pretrained=False):
        super(CNN, self).__init__()
        if resnet:
            self.model = resNet(pre_trained=pretrained)
        else:
            raise NotImplementedError
        self.fc1 = nn.Linear(1000,1024)
        self.head = nn.Linear(1024, 2)

    def forward(self, x):
        x = self.model(x)
        x = self.fc1(x)
        h = self.head(x)
        return h