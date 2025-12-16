# Fixed Error (epsilon = 0.1)
## Monolithic
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SX"; } &>> results/fixed_error_monolithic_sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "COS"; } &>> results/fixed_error_monolithic_cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC"; } &>> results/fixed_error_monolithic_xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS"; } &>> results/fixed_error_monolithic_socxs.txt &
## Compositional
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SX" --compositional; } &>> results/fixed_error_compositional_sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "COS" --compositional; } &>> results/fixed_error_compositional_cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC" --compositional; } &>> results/fixed_error_compositional_xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS" --compositional; } &>> results/fixed_error_compositional_socxs.txt &

# Fixed Time Budget (2 mins)
## Monolithic
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SX"; } &>> results/fixed_time_monolithic_sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "COS"; } &>> results/fixed_time_monolithic_cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "XSOC"; } &>> results/fixed_time_monolithic_xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SOCXS"; } &>> results/fixed_time_monolithic_socxs.txt &
## Compositional
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SX" --compositional; } &>> results/fixed_time_compositional_sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "COS" --compositional; } &>> results/fixed_time_compositional_cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "XSOC" --compositional; } &>> results/fixed_time_compositional_xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SOCXS" --compositional; } &>> results/fixed_time_compositional_socxs.txt &

wait
