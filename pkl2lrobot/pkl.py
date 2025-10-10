"""
读取并显示某一个pkl文件，并解析和显示其内容
"""

import pickle
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class PklReader:
    """
    读取并解析 pkl 文件的类。
    
    Attributes:
        file_path: pkl 文件路径
        data: 从文件中加载的数据
        is_loaded: 是否已加载数据
    """
    file_path: Union[str, Path]
    data: Optional[Any] = field(default=None, init=False, repr=False)
    is_loaded: bool = field(default=False, init=False, repr=False)
    
    def __post_init__(self):
        """初始化后将路径转换为 Path 对象"""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.pkl':
            raise ValueError(f"文件不是 .pkl 格式: {self.file_path}")
    
    def load(self) -> Any:
        """
        从文件中加载数据
        
        Returns:
            加载的数据
        """
        if self.is_loaded:
            return self.data
        
        try:
            with open(self.file_path, 'rb') as f:
                self.data = pickle.load(f)
            self.is_loaded = True
            logger.debug(f"成功加载文件: {self.file_path.name}")
            return self.data
        except Exception as e:
            logger.error(f"加载文件失败: {e}")
            raise RuntimeError(f"加载文件失败: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要信息
        
        Returns:
            包含数据类型、长度等信息的字典
        """
        if not self.is_loaded:
            self.load()
        
        summary = {
            'file_path': str(self.file_path),
            'file_size': f"{self.file_path.stat().st_size / 1024/1024:.2f} MB",
            'data_type': type(self.data).__name__,
        }
        
        # 根据数据类型添加更多信息
        if isinstance(self.data, list):
            summary['length'] = len(self.data)
            if len(self.data) > 0:
                summary['first_item_type'] = type(self.data[0]).__name__
                if isinstance(self.data[0], dict):
                    summary['first_item_keys'] = list(self.data[0].keys())
        
        elif isinstance(self.data, dict):
            summary['keys'] = list(self.data.keys())
            summary['num_keys'] = len(self.data)
        
        elif isinstance(self.data, np.ndarray):
            summary['shape'] = self.data.shape
            summary['dtype'] = str(self.data.dtype)
        
        return summary
    
    def display(self, max_items: int = 5, verbose: bool = False):
        """
        显示数据内容
        
        Args:
            max_items: 最多显示的条目数（针对列表或字典）
            verbose: 是否显示详细信息
        """
        if not self.is_loaded:
            self.load()
        
        logger.info("\n" + "=" * 60)
        logger.info(f"文件: {self.file_path.name}")
        logger.info("=" * 60)
        
        # 显示摘要
        summary = self.get_summary()
        logger.info("\n📊 数据摘要:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
        
        # 显示详细内容
        logger.info("\n📄 数据内容:")
        
        if isinstance(self.data, list):
            logger.info(f"\n列表长度: {len(self.data)}")
            display_count = min(max_items, len(self.data))
            for i in range(display_count):
                logger.info(f"\n[{i}]:")
                self._display_item(self.data[i], indent=2, verbose=verbose)
            if len(self.data) > max_items:
                logger.info(f"\n... (省略 {len(self.data) - max_items} 项)")
        
        elif isinstance(self.data, dict):
            keys = list(self.data.keys())
            display_keys = keys[:max_items]
            for key in display_keys:
                logger.info(f"\n'{key}':")
                self._display_item(self.data[key], indent=2, verbose=verbose)
            if len(keys) > max_items:
                logger.info(f"\n... (省略 {len(keys) - max_items} 个键)")
        
        else:
            self._display_item(self.data, indent=0, verbose=verbose)
        
        logger.info("\n" + "=" * 60)
    
    def _display_item(self, item: Any, indent: int = 0, verbose: bool = False):
        """
        显示单个条目
        
        Args:
            item: 要显示的条目
            indent: 缩进空格数
            verbose: 是否显示详细信息
        """
        prefix = " " * indent
        
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, np.ndarray):
                    logger.info(f"{prefix}{key}: array(shape={value.shape}, dtype={value.dtype})")
                    if verbose and value.size < 50:
                        logger.debug(f"{prefix}  值: {value}")
                elif isinstance(value, (list, tuple)) and len(value) > 10:
                    logger.info(f"{prefix}{key}: {type(value).__name__}(len={len(value)})")
                    if verbose:
                        logger.debug(f"{prefix}  前3项: {value[:3]}")
                else:
                    logger.info(f"{prefix}{key}: {value}")
        
        elif isinstance(item, np.ndarray):
            logger.info(f"{prefix}array(shape={item.shape}, dtype={item.dtype})")
            if verbose and item.size < 50:
                logger.debug(f"{prefix}值: {item}")
        
        elif isinstance(item, (list, tuple)) and len(item) > 10:
            logger.info(f"{prefix}{type(item).__name__}(len={len(item)})")
            if verbose:
                logger.debug(f"{prefix}前3项: {item[:3]}")
        
        else:
            logger.info(f"{prefix}{item}")
    
    def get_field_info(self) -> Dict[str, Any]:
        """
        获取字段信息（针对 list[dict] 类型的数据）
        
        Returns:
            包含字段统计信息的字典
        """
        if not self.is_loaded:
            self.load()
        
        if not isinstance(self.data, list) or len(self.data) == 0:
            return {"error": "数据不是非空列表"}
        
        if not isinstance(self.data[0], dict):
            return {"error": "列表项不是字典类型"}
        
        # 统计所有出现过的字段
        all_keys = set()
        for item in self.data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        # 统计每个字段的信息
        field_info = {}
        for key in sorted(all_keys):
            present_count = 0
            shapes = set()
            dtypes = set()
            
            for item in self.data:
                if isinstance(item, dict) and key in item and item[key] is not None:
                    present_count += 1
                    value = item[key]
                    
                    if isinstance(value, np.ndarray):
                        shapes.add(value.shape)
                        dtypes.add(str(value.dtype))
                    elif isinstance(value, (list, tuple)):
                        shapes.add(f"len={len(value)}")
            
            field_info[key] = {
                'present': present_count,
                'total': len(self.data),
                'coverage': f"{present_count / len(self.data) * 100:.1f}%",
            }
            
            if shapes:
                field_info[key]['shapes'] = list(shapes)
            if dtypes:
                field_info[key]['dtypes'] = list(dtypes)
        
        return field_info
    
    def display_field_info(self):
        """显示字段信息统计"""
        field_info = self.get_field_info()
        
        if 'error' in field_info:
            logger.error(f"{field_info['error']}")
            return
        
        logger.info("\n" + "=" * 60)
        logger.info("📋 字段统计信息")
        logger.info("=" * 60)
        
        for key, info in field_info.items():
            logger.info(f"\n字段: '{key}'")
            logger.info(f"  出现次数: {info['present']}/{info['total']} ({info['coverage']})")  
            if 'shapes' in info:
                logger.info(f"  形状: {info['shapes']}")
            if 'dtypes' in info:
                logger.info(f"  数据类型: {info['dtypes']}")
def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='读取并显示 pkl 文件内容')
    parser.add_argument('pkl_file', type=str, help='pkl 文件路径')
    parser.add_argument('--max-items', type=int, default=3, help='最多显示的条目数')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    parser.add_argument('--field-info', action='store_true', help='显示字段统计信息')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='日志级别')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(message)s'
    )
    
    try:
        reader = PklReader(args.pkl_file)
        reader.display(max_items=args.max_items, verbose=args.verbose)
        # logger.info(reader.data)
        # if args.field_info:
        #     reader.display_field_info()
    
    except Exception as e:
        logger.error(f"错误: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

# uv run ./scripts/pkl.py  ./scripts/0.pkl