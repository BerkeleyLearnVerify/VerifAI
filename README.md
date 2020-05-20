[![Documentation Status](https://readthedocs.org/projects/verifai/badge/?version=latest)](https://verifai.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)


# VerifAI

**VerifAI** is a software toolkit for the formal design and analysis of 
systems that include artificial intelligence (AI) and machine learning (ML)
components.
VerifAI particularly seeks to address challenges with applying formal methods to perception and ML components, including those based on neural networks, and to model and analyze system behavior in the presence of environment uncertainty.
VerifAI’s core paradigm, simulation guided by formal models and specifications, enables a variety of use cases including temporal-logic falsification, model-based systematic fuzz testing, parameter synthesis, counterexample analysis, and data set augmentation.

Please see the [documentation](https://verifai.readthedocs.io/) for installation instructions, tutorials, publications using VerifAI, and more.

VerifAI was designed and implemented by Tommaso Dreossi, Daniel J. Fremont, Shromona Ghosh, Edward Kim, Hadi Ravanbakhsh, Marcell Vazquez-Chanlatte, and Sanjit A. Seshia.

If you have any problems using VerifAI, please submit an issue to the GitHub repository or contact Daniel Fremont at [dfremont@ucsc.edu](mailto:dfremont@ucsc.edu) or Edward Kim at [ek65@berkeley.edu](mailto:ek65@berkeley.edu).

### Repository Structure

* _docs_: sources for the [documentation](https://verifai.readthedocs.io/);

* _examples_: examples and additional documentation for particular simulators, including CARLA, Webots, X-Plane, and OpenAI Gym;

* _verifai_: the source for the `verifai` package proper.