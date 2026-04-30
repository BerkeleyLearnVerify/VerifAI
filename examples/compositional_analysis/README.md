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

This will print compositional SMC and falsification results for the scenarios specified in the script.
Note that falsification might return `None` as example traces do not contain a sufficient number of samples.


## API: ScenarioBase and CompositionalAnalysisEngine

This section describes the core data structures used for compositional statistical model checking and falsification.


## ScenarioBase

`ScenarioBase` is responsible for loading raw trace data and computing **per-scenario empirical statistics**.

### Constructor

```python
ScenarioBase(
    logbase: Dict[str, str] | Dict[str, pd.DataFrame],
    delta: float = 0.05
)
```

### Arguments

* **`logbase`**

  * Dictionary mapping scenario names → trace data
  * Each value can be either:

    * a file path (`str`) to a CSV file, or
    * a `pandas.DataFrame`

  Each trace dataset must contain:

  | Column   | Type       | Description                             |
  | -------- | ---------- | --------------------------------------- |
  | trace_id | str        | Identifier for a trajectory             |
  | step     | int        | Time step within trajectory             |
  | label    | bool/float | Success (1) or failure (0) at each step |

* **`delta`**

  * Confidence parameter for Hoeffding-style bounds
  * Default: `0.05` (95% confidence interval)


### Key Attributes

* `data: Dict[str, pd.DataFrame]`

  * Loaded trace data per scenario

* `success_stats: Dict[str, ScenarioStats]`

  * Precomputed statistics per scenario:

    ```python
    ScenarioStats(rho: float, uncertainty: float)
    ```
  * `rho`: empirical success probability
  * `uncertainty`: Hoeffding bound estimate


### Core Methods

#### `get_success_prob(scenario: str) -> float`

Returns empirical success probability:

```python
rho
```


#### `get_success_prob_uncertainty(scenario: str) -> float`

Returns uncertainty bound:

```python
epsilon
```


## CompositionalAnalysisEngine

The `CompositionalAnalysisEngine` performs **compositional inference over scenario sequences** using importance sampling and KDE-based density ratio estimation.


### Constructor

```python
CompositionalAnalysisEngine(scenario_base: ScenarioBase)
```

### Arguments

* **`scenario_base`**

  * A `ScenarioBase` instance containing all primitive scenario traces and statistics


## check()

Estimates specification satisfaction probability using compositionally satistical verification over a sequence of scenarios.

```python
check(
    scenario: List[str],
    features: List[str],
    center_feat_idx: Optional[List[int]] = None,
    bw_method: Union[str, int] = 10,
) -> Tuple[float, float]
```


### Arguments

* **`scenario`**

  * Ordered list of scenario names
  * Example: `["A", "B", "C"]`
  * Interpreted as a sequential composition:
    A -> B -> C

* **`features`**

  * List of column names used for KDE-based importance sampling
  * Must exist in all scenario DataFrames

* **`center_feat_idx`** *(optional)*

  * Indices of feature dimensions to mean-center before KDE

* **`bw_method`**

  * Bandwidth parameter for `scipy.stats.gaussian_kde`
  * Can be:

    * `"scott"`, `"silverman"`, or numeric scalar


### Returns

```python
(rho, uncertainty)
```

* **`rho`**

  * Estimated compositional success probability

* **`uncertainty`**

  * Propagated uncertainty bound across scenario chain


### Notes

* Uses **importance sampling between consecutive scenarios**
* Applies **Gaussian KDE density ratio estimation**
* Uses **union bound over steps for uncertainty propagation**
* Returns `(0.0, 0.0)` if insufficient samples exist


## falsify()

Generates a counterexample trace (CE) compositionally for a scenario sequence by stitching together traces from primitive scenarios.

```python
falsify(
    scenario: List[str],
    features: List[str],
    center_feat_idx: Optional[List[int]] = None,
    align_feat_idx: Optional[List[int]] = None,
    bw_method: Union[str, int] = 10,
) -> Tuple[Optional[pd.DataFrame], float]
```


### Arguments

* **`scenario`**

  * Ordered list of scenario names
  * Example: `["A", "B", "C"]`
  * Interpreted as a sequential composition:
    A -> B -> C

* **`features`**

  * Feature columns used for similarity search between traces

* **`center_feat_idx`** *(optional)*

  * Feature indices to mean-center before comparison

* **`align_feat_idx`** *(optional)*

  * Feature indices used to align traces via translation offset
  * Ensures smooth transition between concatenated traces

* **`bw_method`**

  * Bandwidth parameter for KDE (same as in `check`)


### Returns

* **`trace: pd.DataFrame | None`**

  * A counterexample trajectory (concatenated trace)
  * `None` if no failure trace can be constructed



### Behavior Summary

* For **single scenario**:

  * selects a failing trace (if available)
  * otherwise returns `None`

* For **compositional scenarios**:

  * works backwards from last scenario
  * selects failure traces via:

    * KDE likelihood (when enough samples exist)
    * Euclidean fallback (low-sample regime)
  * concatenates selected traces into a full counterexample


## Design Intuition

* `ScenarioBase` = empirical grounding (Monte Carlo traces)
* `CompositionalAnalysisEngine` = lifts primitives → sequential compositions
* KDE = approximates unknown transition densities between scenario stages
* Importance sampling = corrects distribution mismatch across scenarios

