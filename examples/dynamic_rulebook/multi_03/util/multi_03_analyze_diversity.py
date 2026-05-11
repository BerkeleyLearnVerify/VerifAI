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
adv1_speed = []
adv2_speed = []
adv_speed = []
ego_speed = []
for file in all_files:
    with file.open("r") as infile:
        lines = infile.readlines()
    if mode == "single":
        for i in range(1, len(lines)):
            line = lines[i]  # TODO: identify the counterexamples
            ego_speed.append(float(line.split(",")[-10]))
            adv_speed.append(float(line.split(",")[-11]))
            adv2_speed.append(float(line.split(",")[-12]))
            adv1_speed.append(float(line.split(",")[-13]))
    else:
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(",")[-17]))
            adv_speed.append(float(line.split(",")[-18]))
            adv2_speed.append(float(line.split(",")[-19]))
            adv1_speed.append(float(line.split(",")[-20]))

ax.scatter(ego_speed, adv_speed, adv2_speed)
ax.set_xlabel("EGO_SPEED")
ax.set_ylabel("ADV_SPEED")
ax.set_zlabel("ADV2_SPEED")
plt.savefig(str(directory / f"{sys.argv[2]}_scatter.png"))

print("Standard deviation of ego_speed:", np.std(ego_speed), len(ego_speed))
print("Standard deviation of adv_speed:", np.std(adv_speed), len(adv_speed))
print("Standard deviation of adv1_speed:", np.std(adv1_speed), len(adv1_speed))
print("Standard deviation of adv2_speed:", np.std(adv2_speed), len(adv2_speed))
