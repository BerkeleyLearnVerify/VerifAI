# Compositional Analysis for Markovian Specifications

This directory provides an example use case of **compositional analysis** for *Markovian* (i.e., memoryless) specifications.

The core idea is to perform **Statistical Model Checking (SMC)** or **falsification** on *primitive scenarios* — scenarios that serve as building blocks for defining more complex *composite scenarios*. The analysis traces generated from these primitives are stored in a `ScenarioBase` object.

These traces can then be supplied to an instance of `CompositionalAnalysisEngine`, which supports querying over composite scenario structures to perform compositional analysis based on the primitive scenario traces.

This example uses the [MetaDrive](https://metadriverse.github.io/metadrive/) simulator.

* Train a reinforcement learning policy using `train.py`.
* Test the policy and save generated traces using `test.py`.
* See `analyze.py` for an example of how to perform compositional analysis on generated traces.

