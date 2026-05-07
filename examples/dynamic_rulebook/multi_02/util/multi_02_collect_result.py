import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np

from result_reporter import print_result_summary

infile_path = Path(sys.argv[1])  # *.txt
mode = sys.argv[2]  # multi / single
order = sys.argv[3]  # -1 / 0 / 1

# error weights
result_count_0 = [[] for i in range(2)]
result_count_1 = [[] for i in range(2)]
# counterexample types
counterexample_type_0 = [{} for i in range(2)]
counterexample_type_1 = [{} for i in range(2)]
curr_source = 0
with infile_path.open('r') as infile:
    lines = infile.readlines()

count = 0

for i in range(len(lines)):
    if order == '0':
        curr_source = 0
    elif order == '1':
        curr_source = 1
    if mode == 'multi':
        if 'Dynamic Rulebook Rhos' in lines[i]:
            line = lines[i+1].strip().split(' ')
            val1 = []
            for s in line:
                if s != '':
                    val1.append(float(s) < 0)
            assert len(val1) == 2, 'Invalid length of rho'
            result_count_0[curr_source].append(val1[0]*2 + val1[1]*1)
            if tuple(1*np.array([val1[0], val1[1]])) in counterexample_type_0[curr_source]:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1]]))] += 1
            else:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1]]))] = 1

            line = lines[i+2].strip().split(' ')
            val2 = []
            for s in line:
                if s != '':
                    val2.append(float(s) < 0)
            assert len(val2) == 2, 'Invalid length of rho'
            result_count_1[curr_source].append(val2[1]*2 + val2[0]*1)
            if tuple(1*np.array([val2[1], val2[0]])) in counterexample_type_1[curr_source]:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[1], val2[0]]))] += 1
            else:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[1], val2[0]]))] = 1

            if order == '-1':
                curr_source = 1 - curr_source
            
            count += 1
            if count == 900:
                break
    else:
        if 'Dynamic Rulebook Rhos' in lines[i]:
            line = lines[i+1].strip().split(' ')
            val1 = []
            for s in line:
                if s != '':
                    val1.append(float(s) < 0)
            assert len(val1) == 4, 'Invalid length of rho'
            result_count_0[curr_source].append(val1[0]*2 + val1[1]*1)
            if tuple(1*np.array([val1[0], val1[1]])) in counterexample_type_0[curr_source]:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1]]))] += 1
            else:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1]]))] = 1

            line = lines[i+2].strip().split(' ')
            val2 = []
            for s in line:
                if s != '':
                    val2.append(float(s) < 0)
            assert len(val2) == 4, 'Invalid length of rho'
            result_count_1[curr_source].append(val2[3]*2 + val2[2]*1)
            if tuple(1*np.array([val2[3], val2[2]])) in counterexample_type_1[curr_source]:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[3], val2[2]]))] += 1
            else:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[3], val2[2]]))] = 1

print_result_summary(
    [result_count_0, result_count_1],
    [counterexample_type_0, counterexample_type_1],
)
