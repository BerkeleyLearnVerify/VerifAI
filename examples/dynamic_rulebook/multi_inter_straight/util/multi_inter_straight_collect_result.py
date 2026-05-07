import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np

from result_reporter import print_result_summary

infile_path = Path(sys.argv[1])  # *.txt
mode = sys.argv[2]  # multi / single
order = sys.argv[3]  # alternate / sequential

# error weights
result_count_0 = [[] for i in range(3)]
result_count_1 = [[] for i in range(3)]
result_count_2 = [[] for i in range(3)]
# counterexample types
counterexample_type_0 = [{} for i in range(3)]
counterexample_type_1 = [{} for i in range(3)]
counterexample_type_2 = [{} for i in range(3)]
curr_source = 0
with infile_path.open('r') as infile:
    lines = infile.readlines()

for i in range(len(lines)):
    if mode == 'multi':
        if 'Dynamic Rulebook Rhos' in lines[i]:
            line = lines[i+1].strip().split(' ')
            val1 = []
            val_print = []
            for s in line:
                if s != '':
                    val1.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val1) == 5, 'Invalid length of rho'
            result_count_0[curr_source].append(val1[0]*16 + val1[1]*8 + val1[2]*4 + val1[4]*2 + val1[3]*1)
            if tuple(1*np.array([val1[0], val1[1], val1[2], val1[4], val1[3]])) in counterexample_type_0[curr_source]:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1], val1[2], val1[4], val1[3]]))] += 1
            else:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[1], val1[2], val1[4], val1[3]]))] = 1

            line = lines[i+2].strip().split(' ')
            val2 = []
            val_print = []
            for s in line:
                if s != '':
                    val2.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val2) == 5, 'Invalid length of rho'
            result_count_1[curr_source].append(val2[0]*4 + val2[1]*4 + val2[2]*4 + val2[3]*2 + val2[4]*1)
            if tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[4]])) in counterexample_type_1[curr_source]:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[4]]))] += 1
            else:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[4]]))] = 1

            line = lines[i+3].strip().split(' ')
            val3 = []
            val_print = []
            for s in line:
                if s != '':
                    val3.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val3) == 4, 'Invalid length of rho'
            result_count_2[curr_source].append(val3[0]*8 + val3[1]*4 + val3[2]*2 + val3[3]*1)
            if tuple(1*np.array([val3[0], val3[1], val3[2], val3[3]])) in counterexample_type_2[curr_source]:
                counterexample_type_2[curr_source][tuple(1*np.array([val3[0], val3[1], val3[2], val3[3]]))] += 1
            else:
                counterexample_type_2[curr_source][tuple(1*np.array([val3[0], val3[1], val3[2], val3[3]]))] = 1

            if order == '-1':
                curr_source = curr_source + 1 if curr_source < 2 else 0
    else:
        if 'Dynamic Rulebook Rhos' in lines[i]:
            line = lines[i+1].strip().split(' ')
            val1 = []
            val_print = []
            for s in line:
                if s != '':
                    val1.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val1) == 9, 'Invalid length of rho'
            result_count_0[curr_source].append(val1[0]*16 + val1[3]*8 + val1[4]*4 + val1[7]*2 + val1[6]*1)
            if tuple(1*np.array([val1[0], val1[3], val1[4], val1[7], val1[6]])) in counterexample_type_0[curr_source]:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[3], val1[4], val1[7], val1[6]]))] += 1
            else:
                counterexample_type_0[curr_source][tuple(1*np.array([val1[0], val1[3], val1[4], val1[7], val1[6]]))] = 1

            line = lines[i+2].strip().split(' ')
            val2 = []
            val_print = []
            for s in line:
                if s != '':
                    val2.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val2) == 9, 'Invalid length of rho'
            result_count_1[curr_source].append(val2[0]*4 + val2[1]*4 + val2[2]*4 + val2[3]*2 + val2[8]*1)
            if tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[8]])) in counterexample_type_1[curr_source]:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[8]]))] += 1
            else:
                counterexample_type_1[curr_source][tuple(1*np.array([val2[0], val2[1], val2[2], val2[3], val2[8]]))] = 1
    
            line = lines[i+3].strip().split(' ')
            val3 = []
            val_print = []
            for s in line:
                if s != '':
                    val3.append(float(s) < 0)
                    val_print.append(float(s))
            assert len(val3) == 9, 'Invalid length of rho'
            result_count_2[curr_source].append(val3[0]*8 + val3[3]*4 + val3[5]*2 + val3[6]*1)
            if tuple(1*np.array([val3[0], val3[3], val3[5], val3[6]])) in counterexample_type_2[curr_source]:
                counterexample_type_2[curr_source][tuple(1*np.array([val3[0], val3[3], val3[5], val3[6]]))] += 1
            else:
                counterexample_type_2[curr_source][tuple(1*np.array([val3[0], val3[3], val3[5], val3[6]]))] = 1
            
            if order == '-1':
                curr_source = curr_source + 1 if curr_source < 2 else 0

print_result_summary(
    [result_count_0, result_count_1, result_count_2],
    [counterexample_type_0, counterexample_type_1, counterexample_type_2],
)
