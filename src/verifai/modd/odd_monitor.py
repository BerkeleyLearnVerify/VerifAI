from abc import ABC
from tqdm import tqdm
import torch
from torch.utils.data import TensorDataset, random_split, DataLoader
from sklearn.model_selection import train_test_split
import torch.nn as nn
import numpy as np
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
        # self.model.fit(training_set["X"], training_set["y"])
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
        tqdm.write("Use device: {device:}\n".format(device=self.device))

    def train_loop(self, epoch, dataloader, optimizer, loss_function, device):
        # model to training mode (important to correctly handle dropout or batchnorm layers)
        self.model.train()
        self.model.to(device)
        # allocation
        total_loss = 0  # accumulated loss
        n_entries = 0   # accumulated number of data points
        # progress bar def
        train_pbar = tqdm(dataloader, desc="Training Epoch {epoch:2d}".format(epoch=epoch), leave=True)
        # training loop
        for x, label in train_pbar:
            # data to device (CPU or GPU if available)
            x, label = x.to(device), label.to(device)

            optimizer.zero_grad()
            outputs = self.model(x)
            loss = loss_function(outputs.squeeze(), label)
            loss.backward()
            optimizer.step()

            # Update accumulated values
            total_loss += loss.detach().cpu().numpy()
            n_entries += len(x)

            # Update progress bar
            train_pbar.set_postfix({'loss': total_loss / n_entries})
        train_pbar.close()
        return total_loss / n_entries

    def train(self, training_set):
        tqdm.write("Building data loaders...")

        tensor_x = torch.Tensor(training_set["X"]) 
        tensor_y = torch.Tensor(training_set["y"])

        dataset = TensorDataset(tensor_x,tensor_y) 
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        tqdm.write("Done!\n")
        loss_function = nn.BCEWithLogitsLoss()

        tqdm.write("Define optimiser...")
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        tqdm.write("Done!\n")

        lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9)


        tqdm.write("Training...")
        best_loss = np.inf
        # allocation
        train_loss_all, valid_loss_all = [], []

        # loop over epochs
        for epoch in range(1, self.num_epochs + 1):
            # training loop
            train_loss = self.train_loop(epoch, dataloader,  optimizer, loss_function, self.device)

            # collect losses
            train_loss_all.append(train_loss)

            # Print message
            tqdm.write('Epoch {epoch:2d}: \t'
                        'Train Loss {train_loss:.6f}'
                        .format(epoch=epoch,
                                train_loss=train_loss
                                )
                            )

            # Update learning rate with lr-scheduler
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
        # allocation
        total_loss = 0  # accumulated loss
        n_entries = 0   # accumulated number of data points

        # progress bar def
        eval_pbar = tqdm(dataloader, leave=True)
        # evaluation loop
        for x, label in eval_pbar:
            # data to device (CPU or GPU if available)
            x, label = x.to(self.device), label.to(self.device)
            with torch.no_grad():
                outputs = self.model(x)
                loss = loss_function(outputs.squeeze(), label)

            # Update accumulated values
            total_loss += loss.detach().cpu().numpy()
            n_entries += len(x)

            # Update progress bar
            eval_pbar.set_postfix({'loss': total_loss / n_entries})
        eval_pbar.close()
        return total_loss / n_entries