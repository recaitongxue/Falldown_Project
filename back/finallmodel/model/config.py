from dataclasses import dataclass, field
from typing import List


@dataclass
class ModelConfig:
    dataset_root: str = "dataset"
    train_split: str = "train"
    val_split: str = "val"
    test_split: str = "test"
    image_size: int = 224
    sequence_length: int = 24
    stride: int = 6
    batch_size: int = 8
    num_workers: int = 0
    hidden_size: int = 128
    num_layers: int = 2
    dropout: float = 0.2
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 20
    device: str = "cuda"
    checkpoint_dir: str = "checkpoints"
    class_names: List[str] = field(
        default_factory=lambda: ["empty", "standing", "sitting", "lying", "bending", "crawling", "falling"]
    )
    fall_classes: List[int] = field(default_factory=lambda: [3, 6])


@dataclass
class RuleConfig:
    # 论文参数 - 基于典型跌倒检测研究
    fps: float = 20.0
    
    # CGDD (Center of Gravity Drop Detection) 重心下降检测
    cgdd_frame_gap: int = 5
    v_cr: float = 0.015  # 重心下降速度阈值 (论文典型值: 0.01-0.02)
    
    # BTD (Body Tilt Detection) 身体倾斜检测
    theta_cr_deg: float = 55.0  # 倾斜角度阈值 (论文典型值: 45-60度)
    
    # SCDD (Shape Change Detection) 形状变化检测
    p_cr: float = 1.2  # 宽高比阈值 (论文典型值: 1.0-1.5)
    
    # 跌倒后躺卧持续时间
    t_cr_sec: float = 3.0  # 缩短告警时间 (论文典型值: 2-5秒)
    
    # 置信度阈值
    score_threshold: float = 0.55
    
    # 新增：关节角度阈值
    elbow_angle_cr: float = 150.0  # 肘部角度
    knee_angle_cr: float = 160.0   # 膝盖角度
    hip_angle_cr: float = 170.0    # 臀部角度
