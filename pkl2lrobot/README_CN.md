# PKL到LeRobot数据集转换工具

将PKL格式的机器人演示数据转换为LeRobot v2.1数据集格式。

## ⚠️ 重要说明

**转换后的LeRobot数据集必须通过SCP传输到服务器使用**

由于本转换工具使用LeRobot v2.1版本，而当前HuggingFace Hub的更新导致版本不兼容，**无法直接push到Hub使用**。

### 推荐工作流程：

1. **在本地进行转换**（Windows/Linux均可）
2. **将转换后的数据集SCP到服务器**
3. **在服务器上直接使用本地数据集路径训练**

```bash
# 步骤1: 在本地运行转换（不要使用--push-to-hub）
.\pkl2lrobot\convert_v21.ps1  # Windows
# 或
./pkl2lrobot/convert_v21.sh   # Linux/Mac

# 步骤2: 将转换后的数据集传输到服务器
.\pkl2lrobot\copy_to_server.ps1  # Windows
# 或
./pkl2lrobot/copy_to_server.sh   # Linux/Mac

# 步骤3: 在服务器上使用本地路径
# 训练时配置: root="/data2/axgu/.cache", repo_id="move_cup_to_shelf"
```

### 为什么不能用HuggingFace Hub？

LeRobot v2.1数据集格式与当前HuggingFace Hub的更新存在兼容性问题，直接从Hub加载会出现：
- Episode顺序错乱
- 时间戳验证失败
- 数据加载异常

因此**必须使用本地数据集**，通过SCP传输到训练服务器。

## 功能特性

- 支持转换为LeRobot v2.0或v2.1格式
- 视频压缩支持（AV1编解码器）
- 多线程图像/视频写入
- 可配置FPS和图像尺寸
- 基于任务的数据集组织
- HuggingFace Hub集成
- 远程服务器部署支持

## 数据集结构

### 输入格式（PKL）
```
data/offline/
├── 00.pkl
├── 01.pkl
├── 02.pkl
└── ...
```

每个PKL文件包含一个字典列表，包含以下字段：
- `base_rgb`: RGB相机图像 (480, 640, 3)
- `base_depth`: 深度图像 (480, 640, 1)
- `joint_positions`: 关节位置 (8,) - 7个关节 + 夹爪
- `joint_velocities`: 关节速度 (8,)
- `ee_pos_quat`: 末端执行器位姿（位置 + 四元数）
- `gripper_position`: 夹爪状态 (1,)

### 输出格式（LeRobot）
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

## 完整工作流程

### 标准流程：本地转换 → SCP到服务器 → 服务器训练

```bash
# === 步骤1: 在本地转换数据集 ===

# Windows
.\pkl2lrobot\convert_v21.ps1

# Linux/Mac  
./pkl2lrobot/convert_v21.sh

# 转换完成后，数据集位于: ./data/lrobot/move_cup_to_shelf

# === 步骤2: 传输数据集到服务器 ===

# Windows
.\pkl2lrobot\copy_to_server.ps1

# Linux/Mac
./pkl2lrobot/copy_to_server.sh

# 或手动传输
scp -r ./data/lrobot/move_cup_to_shelf axgu@10.16.118.8:/data2/axgu/.cache/

# === 步骤3: 在服务器上训练 ===

ssh axgu@10.16.118.8

# 在训练配置中使用本地路径
# Python代码示例:
# from lerobot.datasets import LeRobotDataset
# dataset = LeRobotDataset(
#     repo_id="move_cup_to_shelf",  # 不需要username/前缀
#     root="/data2/axgu/.cache",     # 本地路径
# )
```

### ⚠️ 注意事项

1. **不要使用 `--push-to-hub` 参数** - 由于HF兼容性问题，推送到Hub后无法正常加载
2. **转换脚本已默认移除此参数** - 直接运行即可
3. **必须使用本地数据集路径** - 训练时配置本地root路径

## 快速开始

### Linux/Mac服务器（推荐）

#### 转换为LeRobot v2.1
```bash
chmod +x ./pkl2lrobot/convert_v21.sh
./pkl2lrobot/convert_v21.sh
```

#### 转换为LeRobot v2.0
```bash
chmod +x ./pkl2lrobot/convert.sh
./pkl2lrobot/convert.sh
```

#### 复制到远程服务器（如果需要）
```bash
chmod +x ./pkl2lrobot/copy_to_server.sh
./pkl2lrobot/copy_to_server.sh
```

### Windows（本地开发/测试）

#### 转换为LeRobot v2.1
```powershell
.\pkl2lrobot\convert_v21.ps1
```

#### 转换为LeRobot v2.0
```powershell
.\pkl2lrobot\convert.ps1
```

#### 复制到远程服务器
```powershell
.\pkl2lrobot\copy_to_server.ps1
```

## 高级用法

### 自定义转换参数

```bash
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
    --task-text "你的任务描述" \
    --tags "标签1" "标签2" "标签3"
```

### 参数说明

- `--src-dir`: PKL文件源目录
- `--output-dir`: LeRobot数据集输出目录
- `--fps`: 视频帧率（默认：30）
- `--use-videos`: 将episodes转换为MP4视频（节省60倍磁盘空间）
- `--robot-type`: 机器人类型标识
- `--repo_id`: HuggingFace Hub仓库ID（格式：用户名/数据集名）
- `--image-writer-threads`: 每个进程的图像写入线程数
- `--image-writer-process`: 图像写入进程数
- `--image-width`: 图像宽度（像素）
- `--image-height`: 图像高度（像素）
- `--task-text`: 任务描述
- `--task-file`: 任务配置YAML文件路径（可选）
- `--push-to-hub`: 转换后上传到HuggingFace Hub
- `--tags`: HuggingFace Hub数据集标签

### 任务配置文件

创建 `task_config.yml` 文件来映射PKL文件名到任务描述：

```yaml
"^move_cup.*": "将杯子移动到架子上"
"^pick_object.*": "抓取并放置物体"
"^open_drawer.*": "打开抽屉"
```

然后使用：
```bash
python dataset_convert.py \
    --task-file task_config.yml \
    --use-task-file \
    ...
```

## 常见问题

### 时间戳容差错误

如果加载数据集时遇到"timestamps unexpectedly violate the tolerance"错误：

**问题根源**: 
- LeRobot v2.1数据集格式与当前HuggingFace Hub更新不兼容
- Hub加载时会打乱episode顺序，导致时间戳验证在episode边界处失败
- 本地转换的数据集完全正确，问题出在Hub的加载逻辑

**解决方案**: **只使用本地数据集，不要push到HuggingFace Hub**

```python
# 正确的加载方式
from lerobot.datasets import LeRobotDataset

dataset = LeRobotDataset(
    repo_id="move_cup_to_shelf",      # 本地数据集名称（不需要username/）
    root="/data2/axgu/.cache",         # 本地路径（数据集所在目录）
    # 不需要从Hub下载
)

# 错误的方式（会导致时间戳错误）
# dataset = LeRobotDataset(
#     repo_id="username/dataset_name",  # ❌ 从Hub加载会出错
# )
```

**数据集部署**:
```bash
# 使用提供的脚本自动传输
./pkl2lrobot/copy_to_server.sh

# 传输完成后，数据集位于服务器: /data2/axgu/.cache/move_cup_to_shelf
```

### 性能优化

- **增加线程/进程数**: 提高 `--image-writer-threads` 和 `--image-writer-process` 以加快转换速度
- **使用视频格式**: 始终使用 `--use-videos` 标志 - 减少约60倍磁盘使用，训练数据加载速度提升约25倍
- **批处理**: 对于大型数据集，分批处理以避免内存问题

### PKL文件传输慢？

对于大量PKL文件，可以先压缩再传输：

```bash
# 本地压缩
tar -czf offline.tar.gz data/offline/

# 传输压缩文件
scp offline.tar.gz axgu@10.16.118.8:/data2/axgu/

# 服务器上解压
ssh axgu@10.16.118.8
cd /data2/axgu
tar -xzf offline.tar.gz
```

## LeRobot版本兼容性

### v2.1（推荐）
- 最新功能和改进
- 更好的时间戳处理
- 使用 `convert_v21.ps1` 或 `convert_v21.sh`

### v2.0（旧版）
- 用于兼容性
- 使用 `convert.ps1` 或 `convert.sh`

## 远程部署

`copy_to_server` 脚本通过SCP将转换后的数据集传输到远程服务器。

默认配置：
- 服务器: `10.16.118.8`
- 用户: `axgu`
- 路径: `/data2/axgu/.cache/move_cup_to_shelf`

根据你的环境编辑脚本以更改这些设置。

## 系统要求

- Python 3.11+
- `uv` 包管理器
- LeRobot库
- OpenCV
- PyYAML
- NumPy
- SSH/SCP（用于远程部署）

## 典型使用场景

### 场景1: 标准工作流程（推荐）

```bash
# 1. 本地采集数据 → PKL文件在 ./data/offline/
# （已完成数据采集）

# 2. 本地转换为LeRobot格式
.\pkl2lrobot\convert_v21.ps1  # Windows
# 或
./pkl2lrobot/convert_v21.sh   # Linux

# 3. 验证转换结果
ls ./data/lrobot/move_cup_to_shelf
# 应该看到: data/, videos/, meta/

# 4. 传输到服务器
.\pkl2lrobot\copy_to_server.ps1  # Windows
# 或  
./pkl2lrobot/copy_to_server.sh   # Linux

# 5. 服务器上训练
ssh axgu@10.16.118.8
cd /path/to/training/code

# 在训练脚本中:
# dataset = LeRobotDataset(
#     repo_id="move_cup_to_shelf",
#     root="/data2/axgu/.cache",
# )
```

### 场景2: 多数据集管理

如果有多个任务数据集：

```bash
# 转换多个数据集
./pkl2lrobot/convert_v21.sh --src-dir data/task1 --output-dir data/lrobot/task1
./pkl2lrobot/convert_v21.sh --src-dir data/task2 --output-dir data/lrobot/task2

# 批量传输
scp -r ./data/lrobot/* axgu@10.16.118.8:/data2/axgu/.cache/

# 服务器上使用
# dataset1 = LeRobotDataset(repo_id="task1", root="/data2/axgu/.cache")
# dataset2 = LeRobotDataset(repo_id="task2", root="/data2/axgu/.cache")
```

## 数据集验证

### 本地验证（转换后）

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# 在本地验证转换结果
dataset = LeRobotDataset(
    repo_id="move_cup_to_shelf",  # 本地数据集名称
    root="./data/lrobot",          # 本地路径
    tolerance_s=10.0,              # 使用较大容差
)

print(f"✅ 数据集验证成功!")
print(f"   总帧数: {len(dataset)}")
print(f"   Episodes: {dataset.meta.total_episodes}")
print(f"   FPS: {dataset.fps}")
```

### 服务器验证（传输后）

```python
# SSH到服务器后
from lerobot.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset(
    repo_id="move_cup_to_shelf",
    root="/data2/axgu/.cache",
    tolerance_s=10.0,
)

print(f"✅ 服务器数据集加载成功!")
print(f"   路径: /data2/axgu/.cache/move_cup_to_shelf")
print(f"   总帧数: {len(dataset)}")
```

## 许可证

参见父目录的LICENSE文件。

## 更新日志

- **2026-01-20**: 
  - 添加Linux/Mac支持（.sh脚本）
  - 添加中文文档
  - **说明HuggingFace Hub兼容性问题**
  - **强调必须使用本地数据集，通过SCP传输到服务器**
  - 提供完整的本地转换→SCP传输→服务器训练工作流程
  - 移除默认的--push-to-hub参数

## 技术背景

### 为什么需要本地数据集？

LeRobot v2.1使用的数据集格式与HuggingFace Hub的最新更新存在不兼容：

1. **Episode顺序问题**: Hub加载时会重新排序parquet文件，导致episodes混乱
2. **时间戳验证失败**: 由于episode顺序错误，相邻帧的时间戳检查会跨越episode边界
3. **数据完整性**: 本地转换的数据集完全正确，只是Hub的加载机制有问题

因此，**最佳实践是在本地转换，然后通过SCP部署到服务器，直接使用本地路径加载**。
