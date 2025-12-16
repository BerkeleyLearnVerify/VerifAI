# Fixed Error (epsilon = 0.1)
## Monolithic
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "SX"; } &> storage/results/fixed_error_monolithic_SX.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "COS"; } &> storage/results/fixed_error_monolithic_COS.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC"; } &> storage/results/fixed_error_monolithic_XSOC.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_error_monolithic --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS"; } &> storage/results/fixed_error_monolithic_SOCXS.txt &
## Compositional
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "SX" --compositional; } &> storage/results/fixed_error_compositional_SX.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "COS" --compositional; } &> storage/results/fixed_error_compositional_COS.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC" --compositional; } &> storage/results/fixed_error_compositional_XSOC.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_error_compositional --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS" --compositional; } &> storage/results/fixed_error_compositional_SOCXS.txt &

# Fixed Time Budget (2 mins)
## Monolithic
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "SX"; } &> storage/results/fixed_time_monolithic_SX.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "COS"; } &> storage/results/fixed_time_monolithic_COS.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "XSOC"; } &> storage/results/fixed_time_monolithic_XSOC.txt &
{ time python run_exp.py --expert --save_dir storage/fixed_time_monolithic --confidence_level 0.95 --time_budget 120 --scenario "SOCXS"; } &> storage/results/fixed_time_monolithic_SOCXS.txt &
## Compositional
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "SX" --compositional; } &> storage/results/fixed_time_compositional_SX.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "COS" --compositional; } &> storage/results/fixed_time_compositional_COS.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "XSOC" --compositional; } &> storage/results/fixed_time_compositional_XSOC.txt &
{ time python run_exp.py --expert --save-dir storage/fixed_time_compositional --confidence_level 0.95 --time_budget 120 --scenario "SOCXS" --compositional; } &> storage/results/fixed_time_compositional_SOCXS.txt &
p