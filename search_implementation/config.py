"""
配置文件：定义项目的全局参数
"""
import numpy as np
from pathlib import Path
from typing import Tuple

# ============ 项目路径配置 ============
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 创建必要的目录
LOG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============ 算法参数配置 ============
class AlgorithmConfig:
    """算法核心参数"""
    
    # Epsilon近似参数
    EPSILON = 0.1  # 近似误差，越小越精确但需要更多采样
    PHI = 0.01     # 概率参数，至少1-φ的概率保证
    DELTA = 0.01   # 额外误差项
    
    # 数据维度
    DIMENSION = 1  # 默认1D，可设置为2或更高
    
    # 采样参数
    BASE_SAMPLES = lambda epsilon: int(1 / epsilon**2)  # 基础采样数量
    MIN_SAMPLES = 100  # 最小采样数量
    SPARSITY_MULTIPLIER = 2  # 稀疏数据的采样倍数
    
    # 算法选择
    USE_SWEEP_LINE = True  # 是否使用扫描线算法（更快）
    
    # 随机种子
    RANDOM_SEED = 42


class QueryConfig:
    """查询参数配置"""
    
    # Range查询默认参数
    DEFAULT_THETA = (0.1, 0.9)  # 权重区间 [a_theta, b_theta]
    
    # Threshold查询默认参数  
    DEFAULT_THRESHOLD = 0.2  # 阈值


class DataConfig:
    """数据处理配置"""
    
    # 直方图参数
    BIN_RANGE = None  # (min_bins, max_bins) or None for auto
    COMPUTE_FREQUENCIES = False  # False表示计算密度
    SCALING_FACTOR = 1.0
    
    # 数据精度
    ROUNDING_PRECISION = 4


# ============ 性能配置 ============
class PerformanceConfig:
    """性能相关配置"""
    
    # 并行处理
    N_WORKERS = 4  # CPU核心数
    
    # 内存优化
    CHUNK_SIZE = 1000  # 批处理大小


# ============ 验证配置 ============
class ValidationConfig:
    """多次抽样验证参数"""
    
    N_TRIALS = 100  # 验证试验次数
    ACCEPTANCE_THRESHOLD = 0.8  # 准确率阈值
    
    # 自适应epsilon选择
    MIN_EPSILON = 0.01
    MAX_EPSILON = 0.5
    TARGET_ACCURACY = 0.9


# ============ 日志配置 ============
class LogConfig:
    """日志相关配置"""
    
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ENABLE_FILE_LOG = True


# ============ 辅助函数 ============
def get_query_rectangle_1d(r_min: float, r_max: float) -> Tuple[np.ndarray, np.ndarray]:
    """创建1D查询矩形"""
    return np.array([r_min]), np.array([r_max])


def get_query_rectangle_2d(x_min: float, x_max: float, 
                          y_min: float, y_max: float) -> Tuple[np.ndarray, np.ndarray]:
    """创建2D查询矩形"""
    return np.array([x_min, y_min]), np.array([x_max, y_max])


def print_config():
    """打印当前配置"""
    print("=" * 60)
    print("当前配置参数:")
    print("=" * 60)
    print(f"Epsilon (ε): {AlgorithmConfig.EPSILON}")
    print(f"Phi (φ): {AlgorithmConfig.PHI}")
    print(f"Delta (δ): {AlgorithmConfig.DELTA}")
    print(f"维度: {AlgorithmConfig.DIMENSION}D")
    print(f"基础采样数量: {AlgorithmConfig.BASE_SAMPLES(AlgorithmConfig.EPSILON)}")
    print(f"使用扫描线算法: {AlgorithmConfig.USE_SWEEP_LINE}")
    print(f"随机种子: {AlgorithmConfig.RANDOM_SEED}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()


