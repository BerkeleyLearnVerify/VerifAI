# Fixed Error (epsilon = 0.1)
## Monolithic
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "SX"; } &> storage/fixed_error_monolithic/SX/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "COS"; } &> storage/fixed_error_monolithic/COS/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC"; } &> storage/fixed_error_monolithic/XSOC/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS"; } &> storage/fixed_error_monolithic/SOCXS/results.txt &
## Compositional
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "SX" --compositional; } &> storage/fixed_error_compositional/SX/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "COS" --compositional; } &> storage/fixed_error_compositional/COS/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC" --compositional; } &> storage/fixed_error_compositional/XSOC/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS" --compositional; } &> storage/fixed_error_compositional/SOCXS/results.txt &

# Fixed Time Budget (2 mins)
## Monolithic
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "SX"; } &> storage/fixed_time_monolithic/SX/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "COS"; } &> storage/fixed_time_monolithic/COS/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "XSOC"; } &> storage/fixed_time_monolithic/XSOC/results.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "SOCXS"; } &> storage/fixed_time_monolithic/SOCXS/results.txt &
## Compositional
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "SX" --compositional; } &> storage/fixed_time_compositional/SX/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "COS" --compositional; } &> storage/fixed_time_compositional/COS/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "XSOC" --compositional; } &> storage/fixed_time_compositional/XSOC/results.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "SOCXS" --compositional; } &> storage/fixed_time_compositional/SOCXS/results.txt &
p