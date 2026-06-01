# 跌倒检测模型 - Fall Detection Model

## 项目概述

本项目是一个基于深度学习和计算机视觉的跌倒检测系统，结合了 **行为识别模型** 和 **规则引擎** 两种检测方式，实现高精度的跌倒事件检测。

---

## 目录结构

```
finallmodel/
├── model/                    # 核心模型模块
│   ├── __init__.py           # 模块初始化
│   ├── config.py             # 模型配置参数
│   ├── network.py            # GRU网络结构
│   ├── pose_features.py      # 骨骼特征提取器
│   ├── fall_detector.py      # 综合跌倒检测器
│   └── train.py              # 模型训练脚本
├── checkpoints/              # 训练好的模型权重
│   └── best_gru.pt           # 最佳模型权重文件
├── pose_landmarker_lite.task # MediaPipe姿态估计模型
├── requirements.txt          # 依赖项列表
├── test_chinese.py           # 中文测试脚本
├── test_video.py             # 视频测试脚本
├── test_detailed.py          # 详细测试脚本
└── README.md                 # 项目说明文档
```

---

## 技术架构

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    跌倒检测系统架构                          │
├─────────────────────────────────────────────────────────────┤
│  输入视频帧                                                  │
│      │                                                      │
│      ▼                                                      │
│  ┌──────────────────┐                                       │
│  │ MediaPipe Pose   │  骨骼关键点检测（33个关键点）           │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────┐                                       │
│  │ PoseExtractor    │  特征提取（69维特征向量）               │
│  └────────┬─────────┘                                       │
│           │                                                 │
│     ┌─────┴─────┐                                           │
│     ▼           ▼                                           │
│  ┌────────┐ ┌────────────┐                                 │
│  │ GRU    │ │ RuleEngine │  双路检测                         │
│  │行为识别│ │ 规则引擎   │                                   │
│  └────┬───┘ └─────┬──────┘                                 │
│       │           │                                         │
│       └─────┬─────┘                                         │
│             ▼                                               │
│  ┌──────────────────┐                                       │
│  │  融合判定        │  综合两个检测结果                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│      跌倒检测结果                                            │
└─────────────────────────────────────────────────────────────┘
```

### 2. 预训练模型与Backbone

本项目使用了 **MediaPipe Pose Landmarker** 作为预训练的骨骼检测Backbone，这是Google官方提供的高精度实时姿态估计模型。

#### 2.1 MediaPipe Pose Landmarker 模型

**模型文件**：
- `pose_landmarker_lite.task` - 轻量级模型（优先使用）
- `pose_landmarker.task` - 完整模型（备选）

**模型加载逻辑**（`pose_features.py:100-144`）：

```python
class PoseExtractor:
    def __init__(self, min_det_conf=0.3, min_track_conf=0.3):
        # 模型路径搜索顺序：
        # 1. finallmodel/pose_landmarker_lite.task
        # 2. finallmodel/pose_landmarker.task
        # 3. e:/fallmodel/pose_landmarker.task
        # 4. ../pose_landmarker.task
        
        model_path = os.path.join(parent_dir, 'pose_landmarker_lite.task')
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        
        # 创建视频模式检测器（带追踪）
        video_options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=min_det_conf,
            min_tracking_confidence=min_track_conf,
            num_poses=1,  # 单人体检测
        )
        
        # 创建图像模式检测器（无追踪）
        image_options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            ...
        )
        
        self.video_detector = vision.PoseLandmarker.create_from_options(video_options)
        self.image_detector = vision.PoseLandmarker.create_from_options(image_options)
```

**MediaPipe Pose 模型特性**：

| 特性 | 说明 |
|-----|------|
| **模型类型** | TFLite格式（.task文件封装） |
| **输入尺寸** | 支持任意尺寸图像 |
| **关键点数量** | 33个3D关键点（x, y, z, visibility） |
| **检测速度** | 实时（>30 FPS） |
| **预训练数据集** | 大规模人体姿态数据集（Google内部数据集） |
| **模型架构** | 基于MobileNetV2的编码器 + 关键点回归头 |

**33个关键点结构**：

| 关键点分组 | 索引范围 | 关键点名称 |
|-----------|---------|-----------|
| 面部特征 | 0-10 | 鼻子、眼睛、耳朵、嘴巴 |
| 上肢（左） | 11-22 | 左肩、左臂、左手 |
| 上肢（右） | 12-22 | 右肩、右臂、右手 |
| 下肢（左） | 23-31 | 左髋、左腿、左脚 |
| 下肢（右） | 24-32 | 右髋、右腿、右脚 |

**关键点索引定义**（`pose_features.py:33-67`）：

```python
NOSE = 0                    # 鼻子
LEFT_SHOULDER = 11          # 左肩
RIGHT_SHOULDER = 12         # 右肩
LEFT_ELBOW = 13             # 左肘
RIGHT_ELBOW = 14            # 右肘
LEFT_WRIST = 15             # 左手腕
RIGHT_WRIST = 16            # 右手腕
LEFT_HIP = 23               # 左髋
RIGHT_HIP = 24              # 右髋
LEFT_KNEE = 25              # 左膝
RIGHT_KNEE = 26             # 右膝
LEFT_ANKLE = 27             # 左脚踝
RIGHT_ANKLE = 28            # 右脚踝
```

#### 2.2 自定义行为识别模型（FallActionGRU）

**注意**：行为识别模型 **不是预训练模型**，而是本项目**从零开始训练**的GRU网络：

```python
class FallActionGRU(nn.Module):
    def __init__(self, input_size=69, hidden_size=128, num_layers=2, num_classes=7, dropout=0.2):
        self.gru = nn.GRU(
            input_size=input_size,      # 69维特征输入
            hidden_size=hidden_size,    # 128维隐藏层
            num_layers=num_layers,      # 2层双向GRU
            batch_first=True,
            bidirectional=True,
            dropout=dropout
        )
        self.cls = nn.Sequential(
            nn.LayerNorm(256),          # 双向输出拼接后为256维
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes) # 7个行为类别
        )
```

**训练流程**（`train.py`）：

```python
# 1. 初始化模型（无预训练权重）
model = FallActionGRU(
    input_size=33 * 2 + 3,
    hidden_size=128,
    num_layers=2,
    num_classes=7,
    dropout=0.2,
).to(device)

# 2. 定义损失和优化器
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

# 3. 从零开始训练
for epoch in range(20):
    model.train()
    for x, y in train_loader:
        logits = model(x)
        loss = criterion(logits, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # 验证并保存最佳模型
    val_loss, val_acc = evaluate(model, val_loader, criterion, device)
    if val_acc > best_acc:
        torch.save({"state_dict": model.state_dict()}, "checkpoints/best_gru.pt")
```

### 3. 特征提取

从骨骼关键点中提取 **69维特征向量**（`fall_detector.py:326-347`）：

```python
# 特征向量结构
features = [
    # 33个关键点的归一化坐标 (33*2 = 66维)
    keypoints[0].x, keypoints[0].y,
    keypoints[1].x, keypoints[1].y,
    ...
    # 额外3个特征
    center_y,        # 重心Y坐标（臀部中心）
    tilt_deg / 180,  # 身体倾斜角度（归一化）
    wh_ratio         # 身体宽高比
]
```

**行为类别**（`config.py:24-26`）：

| 索引 | 类别 | 说明 |
|-----|------|-----|
| 0 | empty | 空帧（无人） |
| 1 | standing | 站立 |
| 2 | sitting | 坐着 |
| 3 | lying | 躺卧 |
| 4 | bending | 弯腰 |
| 5 | crawling | 爬行 |
| 6 | falling | 跌倒 |

---

## 跌倒检测算法

系统采用 **三重判定条件**（参考论文），三个条件**全部满足**才判定为跌倒：

### 条件1：CGDD - 重心下降检测

**原理**：检测人体重心在短时间内的快速下降

```python
def cgdd_check(frame_interval=5):
    # 获取当前帧和5帧前的重心位置
    cg1 = calculate_center_of_gravity(joints_prev)
    cg2 = calculate_center_of_gravity(joints_current)
    
    # 计算下降速度
    delta_t = frame_interval / fps
    speed_mps = abs(cg2[1] - cg1[1]) / delta_t
    
    # 速度超过阈值判定为跌倒
    return speed_mps >= 0.009  # V_CRITICAL = 0.009 m/s
```

**参数**（`fall_detector.py:112`）：
- `V_CRITICAL = 0.009` m/s（重心下降速度阈值）

### 条件2：BTD - 身体倾斜检测

**原理**：检测身体是否处于水平状态（跌倒后身体接近水平）

```python
def btd_check(joints):
    # 计算头部到腿部中心的角度
    head = joints.head
    leg_center = calculate_leg_center(joints)
    
    dx = abs(head[0] - leg_center[0])
    dy = abs(head[1] - leg_center[1])
    angle = math.degrees(math.atan(dy / dx))
    
    # 角度越小表示越水平
    return angle < 45  # THETA_CRITICAL = 45度
```

**参数**（`fall_detector.py:113`）：
- `THETA_CRITICAL = 45°`（倾斜角度阈值）

### 条件3：SCDD - 形状变化检测

**原理**：检测人体外接矩形的宽高比变化（跌倒后身体变宽）

```python
def scdd_check(bbox):
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin
    ratio = width / height
    
    # 宽高比大于1表示身体呈水平姿态
    return ratio > 1.0  # P_CRITICAL = 1.0
```

**参数**（`fall_detector.py:114`）：
- `P_CRITICAL = 1.0`（宽高比阈值）

### 综合判定逻辑

```python
# 三个条件全部满足才判定为跌倒
is_fall = cgdd_triggered and btd_triggered and scdd_triggered
```

---

## 规则引擎增强（FallRuleEngine）

在基础三重检测之上，规则引擎增加了额外的检测条件（`pose_features.py:252-380`）：

### 条件4：JAD - 关节角度检测

检测肘部、膝盖、臀部的角度变化，跌倒时关节通常会伸直：

```python
def _jad(elbow_angle, knee_angle, hip_angle):
    score = 0
    if elbow_angle > 150:  # 肘部伸直
        score += 1
    if knee_angle > 160:   # 膝盖伸直
        score += 1
    if hip_angle > 170:    # 臀部伸直
        score += 1
    return score >= 2  # 至少两个关节伸直
```

### 条件5：BHD - 身体高度检测

检测身体高度是否显著降低：

```python
def _bhd(body_height):
    # 计算历史平均高度
    avg_height = np.mean(history["body_height"][:-5])
    # 当前高度低于历史平均的70%
    return body_height < avg_height * 0.7
```

---

## 训练配置

### 模型超参数（`config.py`）

| 参数 | 值 | 说明 |
|-----|-----|------|
| `sequence_length` | 24 | 输入序列长度（帧数） |
| `stride` | 6 | 采样步长 |
| `batch_size` | 8 | 批次大小 |
| `hidden_size` | 128 | GRU隐藏层维度 |
| `num_layers` | 2 | GRU层数 |
| `dropout` | 0.2 | Dropout比例 |
| `learning_rate` | 1e-3 | 学习率 |
| `weight_decay` | 1e-4 | L2正则化 |
| `epochs` | 20 | 训练轮数 |

### 数据集结构

```
dataset/
├── train/
│   ├── empty/
│   ├── standing/
│   ├── sitting/
│   ├── lying/
│   ├── bending/
│   ├── crawling/
│   └── falling/
├── val/
└── test/
```

---

## 推理流程

### 单帧检测（`fall_detector.py:456-563`）

```python
def detect_frame(frame, mode='video'):
    # 1. 提取骨骼特征
    pose_features = pose_extractor.extract(frame, mode=mode)
    
    if pose_features is None:
        return {'status': 'no_person', 'is_fall': False}
    
    # 2. 执行行为识别（GRU）
    behavior, behavior_conf = behavior_recognizer.recognize(pose_features)
    
    # 3. 执行规则检测（三重条件）
    fall_result = fall_detector.detect(frame, joints)
    
    # 4. 融合判定
    if fall_result.is_fall:
        behavior = "falling"
    
    # 5. 报警判定（连续多帧确认）
    alert_triggered = sum(alert_frames) >= len(alert_frames) * 0.7
    
    return {
        'is_fall': fall_result.is_fall,
        'behavior': behavior,
        'M1': fall_result.cgdd_triggered,
        'M2': fall_result.btd_triggered,
        'M3': fall_result.scdd_triggered,
        'confidence': fall_result.confidence,
        'alert': alert_triggered
    }
```

---

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 视频检测

```bash
python test_video.py --source input_video.mp4 --save output_video.mp4
```

### 3. Python API

```python
from fall_detector import FallDetector

# 初始化检测器
detector = FallDetector()

# 检测视频文件
result = detector.detect_video(
    video_path='input.mp4',
    mode='fast',
    output_path='output.mp4'
)

# 检测单帧图像
result = detector.detect_image(base64_image_data)

print(f"跌倒检测结果: {result['is_fall']}")
print(f"行为: {result['behavior_cn']}")
print(f"置信度: {result['confidence']:.2f}")
```

---

## 检测结果字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| `status` | str | 检测状态（detecting/no_person/error） |
| `label` | str | 标签（跌倒/正常） |
| `is_fall` | bool | 是否检测到跌倒 |
| `M1` | bool | CGDD条件是否满足 |
| `M2` | bool | BTD条件是否满足 |
| `M3` | bool | SCDD条件是否满足 |
| `center_gravity_speed` | float | 重心下降速度 (m/s) |
| `body_tilt_angle` | float | 身体倾斜角度 (度) |
| `contour_ratio` | float | 身体宽高比 |
| `confidence` | float | 检测置信度 (0-1) |
| `behavior` | str | 行为类别 |
| `behavior_confidence` | float | 行为识别置信度 |
| `alert` | bool | 是否触发报警 |
| `joints` | dict | 关节点坐标 |

---

## 技术特点

1. **双路检测融合**：结合深度学习行为识别和传统规则引擎，提高检测精度
2. **三重判定条件**：基于论文的严谨跌倒判定逻辑
3. **实时处理**：支持视频流实时检测，最低延迟
4. **鲁棒性强**：多条件验证避免误报
5. **可配置性**：所有检测参数均可配置调整

---

## 参考文献

本系统参考以下论文实现：

1. Fall Detection Based on Human Skeleton and Deep Learning
2. Real-Time Fall Detection Using Center of Gravity and Body Shape Analysis
3. MediaPipe Pose: A Framework for Real-Time Pose Estimation