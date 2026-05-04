from abc import ABC

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class Monitor(ABC):
    def __init__(self, model):
        self.model = model

    def train(self, training_set):
        return self.model

    def predict(self, x):
        pass

    def score(self, training_set):
        pass


class GenericMonitor(Monitor):
    def __init__(self, model):
        super().__init__(model)

    def train(self, training_set):
        X_train, X_test, y_train, y_test = train_test_split(
            training_set["X"], training_set["y"], test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy: {accuracy*100:.2f}%")
        return self.model
    
    def predict(self, x):
        return self.model.predict(x)

    def score(self, training_set):
        return self.model.score(training_set["X"], training_set["y"])

class TorchMonitor(Monitor):
    def __init__(self, model):
        super().__init__(model)
        self.learning_rate = 1e-3
        self.weight_decay = 1e-1
        self.num_epochs = 40
        self.batch_size = 16
        self.model = model

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def train_loop(self, epoch, dataloader, optimizer, loss_function, device):
        self.model.train()
        self.model.to(device)
        total_loss = 0 
        n_entries = 0  
        
        for x, label in dataloader:
            x, label = x.to(device), label.to(device)

            optimizer.zero_grad()
            outputs = self.model(x)
            loss = loss_function(outputs.squeeze(), label)
            loss.backward()
            optimizer.step()

            total_loss += loss.detach().cpu().numpy()
            n_entries += len(x)

        return total_loss / n_entries

    def train(self, training_set):

        tensor_x = torch.Tensor(training_set["X"]) 
        tensor_y = torch.Tensor(training_set["y"])

        dataset = TensorDataset(tensor_x,tensor_y) 
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        loss_function = nn.BCEWithLogitsLoss()

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)

        lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9)


        train_loss_all, _ = [], []

        for epoch in range(1, self.num_epochs + 1):
            train_loss = self.train_loop(epoch, dataloader,  optimizer, loss_function, self.device)

            train_loss_all.append(train_loss)


            if lr_scheduler:
                lr_scheduler.step()
        return self.model
    

    def predict(self, x):
        return self.model.predict(x)

    def score(self, training_set):
        tensor_x = torch.Tensor(training_set["X"]) 
        tensor_y = torch.Tensor(training_set["y"])

        dataset = TensorDataset(tensor_x,tensor_y) 
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        loss_function = nn.BCEWithLogitsLoss()

        self.model.eval()
        total_loss = 0 
        n_entries = 0  

        for x, label in dataloader:
            x, label = x.to(self.device), label.to(self.device)
            with torch.no_grad():
                outputs = self.model(x)
                loss = loss_function(outputs.squeeze(), label)

            total_loss += loss.detach().cpu().numpy()
            n_entries += len(x)

        return total_loss / n_entries