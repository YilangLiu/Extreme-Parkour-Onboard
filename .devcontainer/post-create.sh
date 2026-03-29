#!/usr/bin/env bash
set -euo pipefail

cd /workspace

pip install -e ./isaacgym/python
pip install -e ./rsl_rl
pip install -e ./legged_gym
# wandb>=0.19 requires pydantic v2 (ConfigDict); conda image has pydantic v1 for spacy/thinc.
pip install "numpy<1.24" pydelatin "wandb>=0.15,<0.19" tqdm opencv-python ipdb pyfqmr flask
