import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

directory = Path(sys.argv[1])
all_files = [
    f
    for f in directory.iterdir()
    if f.is_file() and f.suffix == ".csv" and f.name.startswith(sys.argv[2] + ".")
]
mode = sys.argv[3]  # multi / single

fig = plt.figure()
ax = fig.add_subplot(projection="3d")
count = 0
ego_speed = []
ego_brake = []
adv_speed = []
adv1_dist = []
for file in all_files:
    with file.open("r") as infile:
        lines = infile.readlines()
    if mode == "single":
        for i in range(1, len(lines)):
            line = lines[i]  # TODO: identify the counterexamples
            ego_speed.append(float(line.split(",")[-10]))
            ego_brake.append(float(line.split(",")[-11]))
            adv_speed.append(float(line.split(",")[-12]))
            adv1_dist.append(float(line.split(",")[-13]))
    else:
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(",")[-15]))
            ego_brake.append(float(line.split(",")[-16]))
            adv_speed.append(float(line.split(",")[-17]))
            adv1_dist.append(float(line.split(",")[-18]))

ax.scatter(ego_speed, adv_speed, adv1_dist)
ax.set_xlabel("EGO_SPEED")
ax.set_ylabel("ADV_SPEED")
ax.set_zlabel("ADV1_DIST")
plt.savefig(str(directory / f"{sys.argv[2]}_scatter.png"))

print("Standard deviation of ego_speed:", np.std(ego_speed), len(ego_speed))
print("Standard deviation of adv_speed:", np.std(adv_speed), len(adv_speed))
print("Standard deviation of ego_brake:", np.std(ego_brake), len(ego_brake))
print("Standard deviation of adv1_dist:", np.std(adv1_dist), len(adv1_dist))
