# Compositional Analysis Example

This directory demonstrates compositional statistical model checking (SMC) for Markovian (i.e., memoryless) specifications using the [MetaDrive](https://metadriverse.github.io/metadrive/) simulator and VerifAI's compositional analysis tools.
The core idea is to perform SMC and falsification on primitive scenarios, scenarios that serve as building blocks for defining more complex composite scenarios. The analysis traces generated from these primitives are stored in a `ScenarioBase` object.
These traces can then be supplied to an instance of `CompositionalAnalysisEngine`, which supports querying over composite scenario structures to perform compositional analysis based on the primitive scenario traces.

## Overview

The scripts here allow you to:

- Generate simulation traces for different driving scenarios using MetaDrive and an expert policy
- Run monolithic or compositional SMC to estimate the probability of success for each scenario
- Analyze and compare results, including compositional falsification (experimental)

## File Descriptions

- `example.py`: Minimal example showing how to use `ScenarioBase` and `CompositionalAnalysisEngine` to analyze pre-generated traces.
- `run_exp.py`: Main script for running experiments. Supports both monolithic and compositional SMC, parallel trace generation, and time/accuracy budgeting.
- `utils.py`: Utilities for environment setup and trace generation using MetaDrive.

## Requirements

Install MetaDrive as follows

```bash
git clone https://github.com/metadriverse/metadrive.git
pip install -e metadrive
```

## How to Run

Run fixed error experiments:

```bash
# Monolithic SMC (single scenario)
python run_exp.py --save_dir storage/fixed_error_monolithic_SX --confidence_level 0.95 --error_bound 0.04295 --scenario "SX"

# Compositional SMC (compositional analysis)
python run_exp.py --save_dir storage/fixed_error_compositional_SX --confidence_level 0.95 --error_bound 0.04295 --scenario "SX" --compositional
```

Run fixed time budget experiments:

```bash
# Monolithic SMC (single scenario)
python run_exp.py --save_dir storage/fixed_time_monolithic_SX --confidence_level 0.95 --time_budget 120 --scenario "SX"

# Compositional SMC (compositional analysis)
python run_exp.py --save_dir storage/fixed_time_compositional_SX --confidence_level 0.95 --time_budget 120 --scenario "SX" --compositional
```

To analyze already generated traces, use `example.py`:

```bash
python example.py
```

This will print compositional  SMC and falsification results for the scenarios specified in the script.
