#!/bin/bash
iteration=100
scenario='multi_inter_left'
use_dynamic_rulebook=true # true / false (false is for a static rulebook)
sampler_idx=1
sampler_type=demab # demab / dmab / dce / random / halton
exploration_ratio=2.0
simulator=scenic.simulators.metadrive.model
simulation_steps=180
log_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}.log"
result_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}.txt"
csv_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}"

rm $scenario/outputs/$log_file
rm $scenario/outputs/$result_file
rm $scenario/outputs/$csv_file.*csv
rm $scenario/outputs/$csv_file\_scatter.png
if [ "$use_dynamic_rulebook" = true ]; then

    for seed in $(seq 0 1);
    do
        python multi.py -n $iteration --headless -e $csv_file.$seed -sp $scenario/$scenario.scenic -gp $scenario/ -rp $scenario/$scenario\_spec.py -sfp $scenario/$scenario\_segment.py -s $sampler_type --seed $seed --using-sampler $sampler_idx -m $simulator --max-simulation-steps $simulation_steps -co $scenario/outputs --exploration-ratio $exploration_ratio >> $scenario/outputs/$log_file
    done

    python $scenario/util/$scenario\_collect_result.py $scenario/outputs/$log_file multi $sampler_idx >> $scenario/outputs/$result_file
    python $scenario/util/$scenario\_analyze_diversity.py $scenario/outputs/ $csv_file multi >> $scenario/outputs/$result_file

else

    for seed in $(seq 0 1);
    do
        python multi.py -n $iteration --headless -e $csv_file.$seed -sp $scenario/$scenario.scenic --single-graph -gp $scenario/$scenario.sgraph -rp $scenario/$scenario\_spec.py -sfp $scenario/$scenario\_segment.py -s $sampler_type --seed $seed --using-sampler 0 -m $simulator --max-simulation-steps $simulation_steps -co $scenario/outputs --exploration-ratio $exploration_ratio >> $scenario/outputs/$log_file
    done

    python $scenario/util/$scenario\_collect_result.py $scenario/outputs/$log_file single 0 >> $scenario/outputs/$result_file
    python $scenario/util/$scenario\_analyze_diversity.py $scenario/outputs/ $csv_file single >> $scenario/outputs/$result_file
fi
