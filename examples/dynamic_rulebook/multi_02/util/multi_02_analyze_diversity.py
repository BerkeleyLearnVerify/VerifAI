import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Local imports from VerifAI (none)

directory = Path(sys.argv[1])
all_files = [f for f in directory.iterdir() if f.is_file() and f.suffix == '.csv' and f.name.startswith(sys.argv[2] + '.')]
mode = sys.argv[3]  # multi / single

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
count = 0
adv3_speed = []
adv_speed = []
ego_brake = []
ego_speed = []

for file in all_files:
    with file.open('r') as infile:
        lines = infile.readlines()
    if mode == 'single':
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(',')[-5]))
            ego_brake.append(float(line.split(',')[-6]))
            adv_speed.append(float(line.split(',')[-7]))
            adv3_speed.append(float(line.split(',')[-8]))
    else:
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(',')[-5]))
            ego_brake.append(float(line.split(',')[-6]))
            adv_speed.append(float(line.split(',')[-7]))
            adv3_speed.append(float(line.split(',')[-8]))

ax.scatter(ego_speed, ego_brake, adv_speed, c='b')
ax.set_xlabel('EGO_SPEED')
ax.set_ylabel('EGO_BRAKE')
ax.set_zlabel('ADV_SPEED')
plt.savefig(str(directory / f"{sys.argv[2]}_scatter.png"))

print("Standard deviation of ego_speed:", np.std(ego_speed), len(ego_speed))
print("Standard deviation of ego_brake:", np.std(ego_brake), len(ego_brake))
print("Standard deviation of adv_speed:", np.std(adv_speed), len(adv_speed))
print("Standard deviation of adv3_speed:", np.std(adv3_speed), len(adv3_speed))
