import sys
import os
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from result_reporter import print_result_summary

infile_path = Path(sys.argv[1])  # *.txt
mode = sys.argv[2]  # multi / single
order = sys.argv[3]

# error weights
result_count_0 = [[] for i in range(3)]
result_count_1 = [[] for i in range(3)]
result_count_2 = [[] for i in range(3)]
# counterexample types
counterexample_type_0 = [defaultdict(int) for _ in range(3)]
counterexample_type_1 = [defaultdict(int) for _ in range(3)]
counterexample_type_2 = [defaultdict(int) for _ in range(3)]
curr_source = 0
with infile_path.open("r") as infile:
    lines = infile.readlines()


def _parse_rho_line(line):
    return [float(s) < 0 for s in line.strip().split(" ") if s != ""]


for i in range(len(lines)):
    if mode == "multi":
        if "Dynamic Rulebook Rhos" in lines[i]:
            val1 = _parse_rho_line(lines[i + 1])
            assert len(val1) == 2, "Invalid length of rho"
            result_count_0[curr_source].append(val1[0] * 1 + val1[1] * 2)
            counterexample_type_0[curr_source][tuple(val1)] += 1

            val2 = _parse_rho_line(lines[i + 2])
            assert len(val2) == 2, "Invalid length of rho"
            result_count_1[curr_source].append(val2[0] * 2 + val2[1] * 1)
            counterexample_type_1[curr_source][tuple(val2)] += 1

            val3 = _parse_rho_line(lines[i + 3])
            assert len(val3) == 1, "Invalid length of rho"
            result_count_2[curr_source].append(val3[0] * 1)
            counterexample_type_2[curr_source][tuple(val3)] += 1

            if order == "-1":
                curr_source = curr_source + 1 if curr_source < 2 else 0
    else:
        if "Dynamic Rulebook Rhos" in lines[i]:
            val1 = _parse_rho_line(lines[i + 1])
            assert len(val1) == 2, "Invalid length of rho"
            result_count_0[curr_source].append(val1[0] * 1 + val1[1] * 2)
            counterexample_type_0[curr_source][tuple(val1)] += 1

            val2 = _parse_rho_line(lines[i + 2])
            assert len(val2) == 2, "Invalid length of rho"
            result_count_1[curr_source].append(val2[0] * 2 + val2[1] * 1)
            counterexample_type_1[curr_source][tuple(val2)] += 1

            val3 = _parse_rho_line(lines[i + 3])
            assert len(val3) == 2, "Invalid length of rho"
            result_count_2[curr_source].append(val3[1] * 1)
            counterexample_type_2[curr_source][(val3[1],)] += 1

            if order == "-1":
                curr_source = curr_source + 1 if curr_source < 2 else 0

print_result_summary(
    [result_count_0, result_count_1, result_count_2],
    [counterexample_type_0, counterexample_type_1, counterexample_type_2],
)
