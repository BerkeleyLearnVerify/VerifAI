# Fixed Error (epsilon = 0.1)
## Monolithic
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SX"; } &>> results/sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "COS"; } &>> results/cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC"; } &>> results/xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS"; } &>> results/socxs.txt &
## Compositional
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SX" --compositional; } &>> results/sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "COS" --compositional; } &>> results/cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "XSOC" --compositional; } &>> results/xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --error_bound 0.1 --scenario "SOCXS" --compositional; } &>> results/socxs.txt &

# Fixed Time Budget (2 mins)
## Monolithic
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SX"; } &>> results/sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "COS"; } &>> results/cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "XSOC"; } &>> results/xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SOCXS"; } &>> results/socxs.txt &
## Compositional
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SX" --compositional; } &>> results/sx.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "COS" --compositional; } &>> results/cos.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "XSOC" --compositional; } &>> results/xsoc.txt &
{ time python run_exp.py --expert --confidence_level 0.95 --time_budget 120 --scenario "SOCXS" --compositional; } &>> results/socxs.txt &

wait
