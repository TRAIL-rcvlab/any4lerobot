# PKL to LeRobot Dataset Converter

Convert PKL format robot demonstration data to LeRobot dataset format.

## Features

- Convert PKL files to LeRobot v2.0 or v2.1 format
- Support for video compression (AV1 codec)
- Multi-threaded image/video writing
- Configurable FPS and image dimensions
- Task-based dataset organization
- HuggingFace Hub integration
- Remote server deployment support

## Dataset Structure

### Input (PKL format)
```
data/offline/
├── 00.pkl
├── 01.pkl
├── 02.pkl
└── ...
```

Each PKL file contains a list of dictionaries with:
- `base_rgb`: RGB camera image (480, 640, 3)
- `base_depth`: Depth image (480, 640, 1)
- `joint_positions`: Joint positions (8,) - 7 joints + gripper
- `joint_velocities`: Joint velocities (8,)
- `ee_pos_quat`: End-effector pose (position + quaternion)
- `gripper_position`: Gripper state (1,)

### Output (LeRobot format)
```
data/lrobot/move_cup_to_shelf/
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet
│       ├── episode_000001.parquet
│       └── ...
├── videos/
│   └── chunk-000/
│       └── observation.images.main/
│           ├── episode_000000.mp4
│           ├── episode_000001.mp4
│           └── ...
└── meta/
    ├── info.json
    ├── episodes.jsonl
    ├── episodes_stats.jsonl
    └── tasks.jsonl
```

## Quick Start

### Windows (PowerShell)

#### Convert to LeRobot v2.1
```powershell
.\pkl2lrobot\convert_v21.ps1
```

#### Convert to LeRobot v2.0
```powershell
.\pkl2lrobot\convert.ps1
```

#### Copy to Remote Server
```powershell
.\pkl2lrobot\copy_to_server.ps1
```

### Linux/Mac (Bash)

#### Convert to LeRobot v2.1
```bash
chmod +x ./pkl2lrobot/convert_v21.sh
./pkl2lrobot/convert_v21.sh
```

#### Convert to LeRobot v2.0
```bash
chmod +x ./pkl2lrobot/convert.sh
./pkl2lrobot/convert.sh
```

#### Copy to Remote Server
```bash
chmod +x ./pkl2lrobot/copy_to_server.sh
./pkl2lrobot/copy_to_server.sh
```

## Advanced Usage

### Custom Conversion

```bash
# Linux/Mac
python dataset_convert.py \
    --src-dir data/your_pkl_data \
    --output-dir ./data/lrobot/your_dataset \
    --fps 30 \
    --use-videos \
    --robot-type "franka research 3" \
    --repo_id "username/dataset_name" \
    --image-writer-threads 4 \
    --image-writer-process 2 \
    --image-width 640 \
    --image-height 480 \
    --task-text "your task description" \
    --tags "tag1" "tag2" "tag3"
```

```powershell
# Windows
python dataset_convert.py `
    --src-dir data/your_pkl_data `
    --output-dir ./data/lrobot/your_dataset `
    --fps 30 `
    --use-videos `
    --robot-type "franka research 3" `
    --repo_id "username/dataset_name" `
    --image-writer-threads 4 `
    --image-writer-process 2 `
    --image-width 640 `
    --image-height 480 `
    --task-text "your task description" `
    --tags "tag1" "tag2" "tag3"
```

### Parameters

- `--src-dir`: Source directory containing PKL files
- `--output-dir`: Output directory for LeRobot dataset
- `--fps`: Frame rate for videos (default: 30)
- `--use-videos`: Convert episodes to MP4 videos (saves 60x disk space)
- `--robot-type`: Robot type identifier
- `--repo_id`: HuggingFace Hub repository ID (format: username/dataset_name)
- `--image-writer-threads`: Number of threads per process for image writing
- `--image-writer-process`: Number of processes for image writing
- `--image-width`: Image width in pixels
- `--image-height`: Image height in pixels
- `--task-text`: Task description
- `--task-file`: Path to task configuration YAML file (optional)
- `--push-to-hub`: Upload to HuggingFace Hub after conversion
- `--tags`: Tags for HuggingFace Hub dataset

### Task Configuration

Create a `task_config.yml` file to map PKL filenames to task descriptions:

```yaml
"^move_cup.*": "move cup to shelf"
"^pick_object.*": "pick and place object"
"^open_drawer.*": "open drawer"
```

Then use:
```bash
python dataset_convert.py \
    --task-file task_config.yml \
    --use-task-file \
    ...
```

## Troubleshooting

### Timestamp Tolerance Errors

If you encounter "timestamps unexpectedly violate the tolerance" errors when loading the dataset:

**Issue**: HuggingFace's dataset loading may shuffle episode order, causing timestamp validation to fail at episode boundaries.

**Solution**: Use local dataset instead of HuggingFace Hub:

```python
# Don't push to hub, use local dataset
dataset_path = "./data/lrobot/move_cup_to_shelf"

# In your training config
data_config.local_dir = dataset_path
data_config.repo_id = None
```

Or copy dataset to training server:
```bash
# Edit copy_to_server.sh to set your server details
./pkl2lrobot/copy_to_server.sh
```

### Performance Optimization

- **More threads/processes**: Increase `--image-writer-threads` and `--image-writer-process` for faster conversion
- **Use videos**: Always use `--use-videos` flag - reduces disk usage by ~60x and speeds up training data loading by ~25x
- **Batch size**: For large datasets, process in batches to avoid memory issues

## LeRobot Version Compatibility

### v2.1 (Recommended)
- Latest features and improvements
- Better timestamp handling
- Use `convert_v21.ps1` or `convert_v21.sh`

### v2.0 (Legacy)
- Older version for compatibility
- Use `convert.ps1` or `convert.sh`

## Remote Deployment

The `copy_to_server` scripts transfer the converted dataset to a remote server via SCP.

Default configuration:
- Server: `10.16.118.8`
- User: `axgu`
- Path: `/data2/axgu/.cache/move_cup_to_shelf`

Edit the script to change these settings for your environment.

## Requirements

- Python 3.11+
- `uv` package manager
- LeRobot library
- OpenCV
- PyYAML
- NumPy
- SSH/SCP (for remote deployment)

## License

See parent directory LICENSE file.
