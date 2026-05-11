import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

p = Path(sys.argv[1])
all_files = [
    f
    for f in p.iterdir()
    if f.is_file() and f.suffix == ".csv" and f.name.startswith(sys.argv[2] + ".")
]
mode = sys.argv[3]  # multi / single

fig = plt.figure()
ax = fig.add_subplot(projection="3d")
count = 0
ego_speed = []
dist_threshold = []
blocking_car_dist = []
bypass_dist = []

for file in all_files:
    with file.open("r") as infile:
        lines = infile.readlines()
    if mode == "single":
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(",")[-3]))
            dist_threshold.append(float(line.split(",")[-4]))
            bypass_dist.append(float(line.split(",")[-5]))
            blocking_car_dist.append(float(line.split(",")[-6]))
    else:
        for i in range(1, len(lines)):
            line = lines[i]
            ego_speed.append(float(line.split(",")[-6]))
            dist_threshold.append(float(line.split(",")[-7]))
            bypass_dist.append(float(line.split(",")[-8]))
            blocking_car_dist.append(float(line.split(",")[-9]))

ax.scatter(ego_speed, dist_threshold, bypass_dist, c="b")
ax.set_xlabel("EGO_SPEED")
ax.set_ylabel("DIST_THRESHOLD")
ax.set_zlabel("BYPASS_DIST")
plt.savefig(str(p / f"{sys.argv[2]}_scatter.png"))

print("Standard deviation of ego_speed:", np.std(ego_speed), len(ego_speed))
print(
    "Standard deviation of dist_threshold:", np.std(dist_threshold), len(dist_threshold)
)
print("Standard deviation of bypass_dist:", np.std(bypass_dist), len(bypass_dist))
print(
    "Standard deviation of blocking_car_dist:",
    np.std(blocking_car_dist),
    len(blocking_car_dist),
)
