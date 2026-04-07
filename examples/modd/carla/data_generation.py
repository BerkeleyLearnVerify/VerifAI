
import math
import os.path
import sys
import os
import shutil
import argparse
import pickle
import numpy as np
import time
import scenic
from dotmap import DotMap
from PIL import Image
import cv2

import pandas as pd



# Arg Parser
parser = argparse.ArgumentParser(description='modd',usage='later', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

## arguments 
parser.add_argument('scenic_path', help='path to scenic file', metavar='scenic_path')
parser.add_argument("--data_dir", type=str, default="./training_data/")
parser.add_argument('--num_sim', help='number of simulations used per monitor', type=int, default=1)
parser.add_argument('--num_steps', help='number of steps per simulation',type=int,default=60)


args = parser.parse_args()



## assignments 

scenic_path = args.scenic_path
num_of_simulations = args.num_sim
num_of_steps = args.num_steps
data_dir = args.data_dir




last_folder = 0


for i in range(last_folder, num_of_simulations):

    
    # Initialize logger folder sstructure
    if i==0:
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        os.mkdir(data_dir)

        
    sim_dir = f"{data_dir}{i}"
    if not os.path.exists(sim_dir):
        os.mkdir(sim_dir)

    flag_good = False
    print(f"Executing sim {i}")
    try:
        os.system(f"scenic -S {scenic_path} --count 1 --time {num_of_steps} --2d --param recordFolder {sim_dir} --param timeout 30")
        flag_good = True
    except: 
        print(f"Simulation {j} failed.")
        wait(5)
        os.system(f"scenic -S {scenic_path} --count 1 --time {num_of_steps} --2d --param recordFolder {sim_dir} --param timeout 30")
        


        



