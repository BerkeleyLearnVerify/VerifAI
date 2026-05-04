import os
import argparse
import re

import numpy as np
import torch
import torchvision
import cv2
from torch.utils.data import Dataset



print("CUDA enabled:", torch.cuda.is_available())


class resNet(torch.nn.Module):
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
        


class CNN(torch.nn.Module):
    def __init__(self, resnet=False, pretrained=False):
        super(CNN, self).__init__()
        if resnet:
            self.model = resNet(pre_trained=pretrained)
        else:
            raise NotImplementedError
        self.fc1 = torch.nn.Linear(1000,1024)
        self.head = torch.nn.Linear(1024, 2)
        print(self.model)

    def forward(self, x):
        x = self.model(x)
        x = self.fc1(x)
        h = self.head(x)
        return h


def train_cnn(
    train_dataset,
    val_dataset,
    save_path,
    batch_size=128,
    n_epochs=351,
    lr=0.0005, 
    device="cuda",
    resnet=True,
    model_name="model"
):
    """
    Train a CNN on the given data
    """
    model = CNN(resnet=resnet).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.9, patience=10
    )
    criterion = torch.nn.MSELoss()
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, drop_last=True
    )
    test_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, drop_last=True)
    best_val_loss = np.inf
    model.eval()

    model_parameters = filter(lambda p: p.requires_grad, model.parameters())
    params = sum([np.prod(p.size()) for p in model_parameters])
    print(f"Number of parameters: {params}")
    with torch.no_grad():
        test_loss = 0
        for x_batch, y_batch in test_loader:
            y_batch = y_batch.reshape((batch_size, 2)).to(device)
            y_pred = model(x_batch.to(device))
            test_loss += criterion(y_pred, y_batch).item()
        test_loss /= len(test_loader)
    print(f"Epoch {-1}: val loss = {test_loss}")
    for epoch in range(n_epochs):
        model.train()
        total_loss = 0
        for loaded_batch in train_loader:
            x_batch, y_batch = loaded_batch
            optimizer.zero_grad()
            y_batch = y_batch.reshape((batch_size, 2)).to(device)
            y_pred = model(x_batch.to(device))
            loss = criterion(y_pred, y_batch)
            total_loss += loss.item()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            test_loss = 0
            for loaded_batch in test_loader:
                x_batch, y_batch = loaded_batch
                y_batch = y_batch.reshape((batch_size, 2)).to(device)
                y_pred = model(x_batch.to(device))
                test_loss += criterion(y_pred, y_batch).item()
            test_loss /= len(test_loader)
        scheduler.step(test_loss)
        print(
            f"Epoch {epoch}: train loss = {total_loss / len(train_loader)} val loss = {test_loss}"
        )
        # save model
        if test_loss < best_val_loss:
            best_val_loss = test_loss
            torch.save(model.state_dict(), os.path.join(save_path, f"{model_name}_{epoch}.pth"))
        if (epoch % 50 == 0 or epoch == n_epochs-1) and epoch > 50 :
            torch.save(model.state_dict(), os.path.join(save_path, f"{model_name}_{epoch}.pth"))
    return model





class CustomDataset(Dataset):

    def __init__(self, imgs, labels, transform=None):
        super().__init__()
        self.imgs = imgs
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return min(len(self.imgs), len(self.labels))

    def __getitem__(self, index):
        img = (torch.from_numpy(self.imgs[index]) / 255).permute(2,0,1)[[2,1,0],:,:]
        label = self.labels[index]

        if self.transform:
            return self.transform(img), torch.FloatTensor([label])
        else:
            return img, torch.FloatTensor([label])


def sort_paths(folder_path):
    orig_paths = [p for p in os.listdir(folder_path) if re.sub("[^0-9]","",p) != ""]
    M = max([len(e) for e in orig_paths])
    m = min([len(e) for e in orig_paths])
    paths = ["0" * (M-len(e)) + e for e in orig_paths]
    paths = sorted(paths)
    for _ in range(M-m-1):
        paths = [e if e[0] != "0" else e[1:] for e in paths]
    paths = [folder_path+e if e[0] != "0" else folder_path+e[1:] for e in paths]
    return paths


        
def load_data_np(
    data_dir,
    split_ratio=0.1,
    seed=0,
):
    """
    Load data and split into train validation
    """
    if data_dir[-1] != "/":
        data_dir += "/"

    dss = []

    paths_data_dirs = [data_dir + e + "/" for e in os.listdir(data_dir) ]
    first = True
    i0 = 0
    for sim in paths_data_dirs:
        if len(os.listdir(sim)) > 0:
            loaded_imgs = [cv2.imread(img) for img in sort_paths(sim)]
            imgs = np.array(loaded_imgs)[:, 80:160, 40:600]
            dist = np.expand_dims(np.load(sim + "dist.npz")["values"], axis=0) / 30
            cte = np.expand_dims(np.load(sim + "cte.npz")["values"], axis=0)
            labels = np.transpose(np.concatenate((cte,dist)))
            if first:   
                first = False
                ds = CustomDataset(imgs, labels)
                i0 = 1
            else:
                dsi = CustomDataset(imgs, labels)
                ds = torch.utils.data.ConcatDataset([ds,dsi])
                i0 +=1
        else:
            print(f"Folder {sim} should be removed. No images in the folder")
    print(f"Total of {len(ds)} images")

    train_dataset, val_dataset = torch.utils.data.random_split(ds, [1-split_ratio, split_ratio])
    
    return train_dataset, val_dataset



parser = argparse.ArgumentParser(description="Train CNN")
parser.add_argument("--data_dir", type=str, default="./training_data/")
parser.add_argument("--model_dir", type=str, default="./models")
parser.add_argument("--model_name", type=str, default="controller_cte_dist")
args = parser.parse_args()

if __name__ == "__main__":


    device="cuda"

    os.makedirs(args.model_dir, exist_ok=True)
    train_dataset, val_dataset = load_data_np(args.data_dir)
    train_cnn(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        save_path=args.model_dir,
        resnet=True,
        model_name=args.model_name, 
    )
    