# Installation of VerifAI and Scenic

1. Clone this repository and [Scenic](https://github.com/BerkeleyLearnVerify/Scenic).
2. Checkout the `kesav-v/multi-objective` branch of VerifAI and the `kesav-v/multi-objective` branch of Scenic.
3. Install `poetry` if you haven’t already done so.
4. Run `poetry shell` from the VerifAI repo and make sure it spawns an environment with Python 3.8+.
5. Run `poetry install`.
6. Go to the location where `Scenic` was cloned and run `poetry install` (while in the same environment that was used for VerifAI).
7. Any other missing packages when running the falsifier script can be installed using `pip`.

# Running the Newtonian Simulator

1. Using the VerifAI environment, go to the `experiments` folder inside VerifAI
2. Run `python experiments.py --newtonian`
3. You should see the Uber crash scenario open up in a pygame window.