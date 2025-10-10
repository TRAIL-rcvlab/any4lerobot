"""
批量将目录中的 pkl（list[dict]）转换为 openpi使用的格式
TODO: 1. pkl加入task描述的支持，现在的pkl没有task描述，只支持单任务
"""
import cv2
import logging
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field 
from typing import Annotated,Any, Dict, List
from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata
# from lerobot.datasets.lerobot_dataset import LeRobotDataset
import shutil
import yaml
import re

from pkl import PklReader

np.set_printoptions(precision=2)

@dataclass
class Task: 
    task_file: Path = Path("./task.yml")
    task_rules: Dict[str,str] = field(default_factory=dict) # 任务规则，正则表达式->任务描述

    def load_task_rules(self):
        if self.task_file.exists():
            with open(self.task_file, "r") as f:
                self.task_rules = yaml.safe_load(f)
    
    def __post_init__(self):
        self.load_task_rules()

    def get_task_by_name(self, name: str) -> str:
        for pattern, task in self.task_rules.items():
            if re.match(pattern, name):
                return task
        return "some task description"
@dataclass
class Data:
    base_rgb: List[Annotated[np.ndarray, (480, 640, 3)]]  # BGR格式
    base_depth: List[Annotated[np.ndarray, (480, 640, 1)]]
    joint_positions: List[Annotated[np.ndarray, (8,)]]
    joint_velocities: List[Annotated[np.ndarray, (8,)]]
    ee_pos_quat: List[tuple[Annotated[np.ndarray, (3,)], Annotated[np.ndarray, (4,)]]]
    gripper_position: List[Annotated[np.ndarray, (1,)]]
    file_name: str = "unknown"

    def check_image(self,image:np.ndarray):
        if image.shape[2]==3:
            # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imshow("image",image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            logging.warning(f"图像通道数不为3，无法显示: shape={image.shape}")

    def preprocess(self,source_data: list[Dict[str, Any]]):
        self.base_rgb = [item['base_rgb'] for item in source_data]
        self.base_depth = [item['base_depth'] for item in source_data]
        self.joint_positions = [item['joint_positions'][:7] for item in source_data] # 只取前7个关节(单臂)
        self.joint_velocities = [item['joint_velocities'][:7] for item in source_data]
        self.ee_pos_quat = [item['ee_pos_quat'] for item in source_data]
        self.gripper_position = [item['gripper_position'] for item in source_data]
        # self.check_image(self.base_rgb[0])    

    def __post_init__(self):#init之后执行的函数，检查图像，对数据做预处理
        self.base_rgb = [cv2.cvtColor(image, cv2.COLOR_RGB2BGR) for image in self.base_rgb]
        pass

    def __init__(self,data_path:Path) -> None:
        source_pkl = PklReader(data_path)
        source_pkl.load()
        self.preprocess(source_pkl.data)
        self.file_name = data_path.stem # stem 用来获取不带后缀的文件名

@dataclass 
class Config:
    src_dir: Path = Path("./convert")
    output_dir: Path = Path("./output")
    log_level: str = "DEBUG"
    use_videos: bool = False
    version: str = "0.1.0"
    image_writer_process: int = 5
    image_writer_threads: int = 10
    robot_type: str = "franka research 3"
    task_text: str = "some task description"
    task_file: Path = Path("./task_config.yml") # 任务配置文件
    fps: int = 30
    repo_id: str = "username/dataset_name"  # The repository name of the dataset to create on the Hugging Face Hub.
    image_width: int = 640
    image_height: int = 480

    DatasetConfig: Dict[str, Any] = field(default_factory=dict)  # for dataset features
    task: Task = field(default_factory=lambda: Task(task_file=Path("./task_config.yml")))
    use_task_file: bool = False  # 是否使用任务文件
    push_to_hub: bool = False  # 是否发布到huggingface
    tags: List[str] = field(default_factory=list)  # 发布到huggingface的标签

    def generate_features_from_raw(self):
        motors_name=[f"robot_arm_{i}" for i in range(7)]
        motors_name+=["gripper"]
        features = {
            "observation.state": {
                "dtype": "float32",
                "shape": (8,),
                "names": {"motors": motors_name},
            },
            "action": {
                "dtype": "float32",
                "dtype": "float32",
                "shape": (8,),
                "names": {"motors": motors_name},
            },
            "observation.velocities": { # 速度
                "dtype": "float32",
                "shape": (8,),
                "names": {"motors": motors_name},
            },
            "observation.images.main": {
                "dtype": "video" if self.use_videos else "image",
                "shape": [480, 640, 3],
                "names": ["height", "width", "rgb"],
            }
        }
        return features

    def __post_init__(self):
       
        if self.DatasetConfig == {}:
            self.DatasetConfig = self.generate_features_from_raw()
        
        if self.task_file != Path("some/default/task/file"):
            self.use_task_file = True
            self.task = Task(task_file=self.task_file)
        # else:
        #     self.use_task_file = False
        #     self.task = Task() # 空任务

@dataclass 
class DatasetConverter:
    config: Config
    data: List[Data] = field(default_factory=list)  # 每一个Data对应一个pkl文件 是一个完整的轨迹

    def create_lerobot_dataset(self):
        lerobot_dataset = LeRobotDataset.create(
            repo_id=self.config.repo_id,
            robot_type=self.config.robot_type,
            root=self.config.output_dir,
            fps=int(self.config.fps),
            use_videos=self.config.use_videos,
            features=self.config.DatasetConfig,
            image_writer_threads=self.config.image_writer_threads,
            image_writer_processes=self.config.image_writer_process,
        )

        episode_length = len(self.data)
        
        for i in range(episode_length):
            episode_data = self.data[i]
            num_steps = len(episode_data.base_rgb)
            for t in range(num_steps - 1):
                state=np.float32(np.concatenate([episode_data.joint_positions[t],episode_data.gripper_position[t]]))
                state_v=np.float32(np.concatenate([episode_data.joint_velocities[t], episode_data.gripper_position[t]]))
                frame_data = {
                    "observation.state": state,
                    "observation.velocities": state_v,
                    "observation.images.main": episode_data.base_rgb[t],
                    # "action": episode_data.joint_positions[t + 1] - episode_data.joint_positions[t],
                    "action": state,
                }

                if config.use_task_file:
                    task_text=self.config.task.get_task_by_name(episode_data.file_name)
                else:
                    task_text=self.config.task_text

                lerobot_dataset.add_frame(frame_data, task_text)

            lerobot_dataset.save_episode()

            # lerobot_dataset.end_episode()

    def push_to_hub(self):
        assert self.config.repo_id is not None
        if self.config.push_to_hub:
            LeRobotDataset(self.config.repo_id, 
                           root=self.config.output_dir).push_to_hub(tags=self.config.tags, private=False, push_videos=True)
   
# -------------------工具代码--------------------
def find_pkl_files(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*.pkl") if p.is_file()]

def check_and_rm_folder(directory: Path)-> bool :
    if directory.exists() and directory.is_dir():
        shutil.rmtree(directory)
        logging.debug(f"已删除存在的目录: {directory}")
    # directory.mkdir(parents=True, exist_ok=True)
    logging.debug(f"创建目录: {directory}")

# -------------------工具代码--------------------


# ------------------ 主函数 -----------------
def main(config: Config = Config()):

    check_and_rm_folder(config.output_dir)
    pkl_files = find_pkl_files(Path(config.src_dir))
    logging.debug(f"找到 {len(pkl_files)} 个 pkl 文件：{pkl_files}")
    DataList = []
    for pkl_file in pkl_files:
        data = Data(pkl_file)
        DataList.append(data)
    
    converter = DatasetConverter(config=config, data=DataList)
    converter.create_lerobot_dataset()
    if config.push_to_hub:
        converter.push_to_hub()
        logging.info(f"数据集{config.repo_id}已发布到 Hugging Face Hub")

    logging.info("数据集转换完成")


        # logging.debug(data)

# --------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='转化数据集格式')

    parser.add_argument("--version", type=str, help="x.y.z", default="0.1.0")
    parser.add_argument('--log-level', type=str, default='DEBUG',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='日志级别')
    parser.add_argument("--src-dir", type=Path, default=Path("some/default/path"), help="Path to the local lerobot dataset.")
    parser.add_argument("--output-dir", type=Path, default=Path("some/default/output"), help="Path to the output directory.")
    parser.add_argument("--use-videos", action="store_true", help="Convert each episode of the raw dataset to an mp4 video. This option allows 60 times lower disk space consumption and 25 faster loading time during training.")
    parser.add_argument("--image-writer-process", type=int, default=5, help="Number of processes of image writer for saving images.")
    parser.add_argument("--image-writer-threads", type=int, default=10, help="Number of threads per process of image writer for saving images.")
    parser.add_argument("--robot-type", type=str, default="franka research 3", help="Type of the robot arm.")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate of the output videos if --use-videos is set.")
    parser.add_argument("--repo_id", type=str, default="username/dataset_name", help="The repository name of the dataset to create on the Hugging Face Hub.")
    parser.add_argument("--task-text", type=str, default="some task description", help="Description of the task.")
    parser.add_argument("--task-file", type=Path, default=Path("some/default/task/file"), help="Path to the task file.")

    # 图像的设置，设置图像的宽高等
    parser.add_argument("--image-width", type=int, default=640, help="Width of the output images.")
    parser.add_argument("--image-height", type=int, default=480, help="Height of the output images.")

    # 发布到huggingface的设置
    parser.add_argument("--push-to-hub", action="store_true", help="upload to hub")
    # tags
    parser.add_argument("--tags", type=str, nargs="+", default=[], help="Tags to add to the dataset on the Hugging Face Hub.")
    args = parser.parse_args()
    config = Config(**vars(args))
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(message)s'
    )
    main(config)


# 可视化使用https://huggingface.co/spaces/lerobot/visualize_dataset 可视即可