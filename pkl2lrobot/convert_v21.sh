#!/bin/bash
# Convert PKL dataset to LeRobot v2.1 format

set -e  # Exit on error

# Create a dedicated v2.1 environment (Python 3.11 recommended)
if [ ! -d ".venv_lerobot_v21" ]; then
    echo "Creating virtual environment..."
    uv venv .venv_lerobot_v21 --python 3.11
fi

# Install lerobot v2.1 from git with LFS smudge disabled (avoid LFS download failures)
echo "Installing lerobot v2.1..."
export GIT_LFS_SKIP_SMUDGE=1
uv pip install --python .venv_lerobot_v21/bin/python \
    "lerobot @ git+https://github.com/huggingface/lerobot.git@d602e8169cbad9e93a4a3b3ee1dd8b332af7ebf8"
uv pip install --python .venv_lerobot_v21/bin/python opencv-python pyyaml numpy

# Ensure output dir is clean
if [ -d "./data/lrobot/move_cup_to_shelf" ]; then
    echo "Removing existing output directory..."
    rm -rf ./data/lrobot/move_cup_to_shelf
fi

# Run conversion with lerobot v2.1
echo "Starting conversion..."
.venv_lerobot_v21/bin/python ./pkl2lrobot/dataset_convert.py \
    --src-dir data/offline \
    --output-dir ./data/lrobot/move_cup_to_shelf \
    --fps 30 \
    --use-videos \
    --robot-type "franka research 3" \
    --repo_id "luobai/move_cup_to_shelf1" \
    --image-writer-threads 4 \
    --image-writer-process 2 \
    --image-width 640 \
    --image-height 480 \
    --task-text "move cup to shelf" \
    --push-to-hub \
    --tags "franka research 3" "manipulation" "pick and place"

echo "✅ Conversion completed!"
